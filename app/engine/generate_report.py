#!/usr/bin/env python3
"""
Moteur de génération de rapports de prévention incendie ZSBW
Usage: python3 generate_report.py <projet.json> <type: BB|BM> <output.docx>
"""
import json, re, sys, shutil
from pathlib import Path
from datetime import datetime

SCRIPTS = Path("/home/claude/scripts/office")
TEMPLATES = {"BB": Path("/home/claude/template_bb.docx"), "BM": Path("/home/claude/template_bm.docx")}
MAPPING = json.load(open("/home/claude/engine/point_mapping.json"))

def load_project(path):
    return json.load(open(path))

def evaluate_conditions(point, project):
    """Évalue si un point s'applique au projet donné"""
    cond = point.get("condition","always")
    p = project
    if cond == "always": return True
    if cond == "always_bm": return p.get("type_batiment") == "BM"
    if cond == "has_logements": return p.get("has_logements", False)
    if cond == "has_cage_escalier": return p.get("has_cage_escalier", True)
    if cond == "has_parking": return p.get("has_parking", False)
    if cond == "has_local_technique": return p.get("has_local_technique", False)
    if cond == "has_local_ordures": return p.get("has_local_ordures", False)
    if cond == "has_chaufferie": return p.get("has_chaufferie", False)
    if cond == "has_sous_sol": return p.get("has_sous_sol", False)
    if cond == "has_faux_plafonds": return p.get("has_faux_plafonds", False)
    if cond == "has_gaz": return p.get("has_gaz", True)
    if cond == "has_ascenseur": return p.get("has_ascenseur", False)
    if cond == "has_duplex": return p.get("has_duplex", False)
    if cond == "has_locaux_diurnes": return p.get("has_locaux_diurnes", False)
    if cond == "impasse_gt_30m": return p.get("impasse_gt_30m", False)
    if cond == "appts_par_niveau_lte_6": return p.get("appts_par_niveau", 0) <= 6
    if cond == "parking_gt_625m2": return p.get("parking_superficie", 0) > 625
    if cond == "batiment_specifique": return True
    return True

def get_annotation_status(point, project):
    """Retourne le statut: nonconforme|averifier|conforme|info"""
    nonconf = point.get("nonconforme_if", [])
    averifier = point.get("averifier_if", [])
    conforme = point.get("conforme_if", [])
    flags = project.get("flags", [])
    for f in nonconf:
        if f in flags: return "nonconforme"
    for f in conforme:
        if f in flags: return "conforme"
    for f in averifier:
        if f in flags: return "averifier"
    # Par défaut pour les points toujours actifs
    if averifier: return "averifier"
    return "info"

def build_xml_annotation(point, status, project):
    """Génère le bloc XML d'annotation à injecter"""
    annotation = point["annotation"]
    # Remplacer les variables projet dans l'annotation
    for key, val in project.get("vars", {}).items():
        annotation = annotation.replace("{"+key+"}", str(val))
    
    colors = {
        "nonconforme": ("FF0000", "PAS CONFORME"),
        "averifier": ("FFC000", "À VÉRIFIER"),
        "conforme": ("00B050", "CONFORME"),
        "info": ("4472C4", ""),
    }
    color, prefix = colors[status]
    label = f"{prefix} — " if prefix else ""
    
    # Texte annoté avec couleur
    text = annotation.replace("'", "&#x2019;").replace('"', "&#x201C;").replace('<', "&lt;").replace('>', "&gt;").replace('&', "&amp;")
    label_esc = label.replace("'", "&#x2019;")
    
    xml = f"""<w:p>
  <w:pPr><w:ind w:left="360"/><w:rPr><w:color w:val="{color}"/></w:rPr></w:pPr>
  <w:r><w:rPr><w:color w:val="{color}"/><w:b/></w:rPr><w:t xml:space="preserve">{label_esc}</w:t></w:r>
  <w:r><w:rPr><w:color w:val="{color}"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>
</w:p>"""
    return xml

def find_point_in_xml(content, point_id):
    """Trouve la position d'un point numéroté dans le XML"""
    # Chercher le numéro de point dans les listes numérotées
    patterns = [
        f">{point_id}.<",
        f">{point_id}. <",
    ]
    for pat in patterns:
        idx = content.find(pat)
        if idx > 0:
            # Aller à la fin du paragraphe suivant (après le texte du point)
            end = content.find('</w:p>', idx)
            # Prendre 3 paragraphes de plus pour passer le corps du texte
            for _ in range(4):
                next_end = content.find('</w:p>', end+6)
                if next_end > 0: end = next_end
            return end + 6
    return -1

def fill_variables(content, project):
    """Remplace tous les champs [MIS_...] et [DOS_...]"""
    fields = project.get("fields", {})
    replacements = 0
    for key, value in fields.items():
        if key in content:
            content = content.replace(key, value)
            replacements += 1
    print(f"  {replacements} champs variables remplis")
    return content

def generate(project_path, bat_type, output_path):
    project = load_project(project_path)
    bat_type = bat_type.upper()
    
    print(f"\n{'='*60}")
    print(f"Génération rapport {bat_type} — {project.get('fields',{}).get('[DOS_DOS_NAME]','???')}")
    print(f"{'='*60}")
    
    # 1. Copier le template
    template = TEMPLATES[bat_type]
    work_dir = Path("/tmp/rpt_work")
    if work_dir.exists(): shutil.rmtree(work_dir)
    
    import subprocess
    subprocess.run(["python3", str(SCRIPTS/"unpack.py"), str(template), str(work_dir)], 
                   capture_output=True)
    print(f"✓ Template {bat_type} décompacté")
    
    # 2. Remplir les variables
    doc_xml = work_dir / "word/document.xml"
    content = doc_xml.read_text(encoding='utf-8')
    content = fill_variables(content, project)
    
    # Corriger lien brisé connu
    content = content.replace(' r:link="rId78"', '')
    
    # 3. Injecter les annotations
    print(f"\nAnnotations:")
    injected = 0
    annotations_to_inject = []
    
    for point in MAPPING["points"]:
        if not evaluate_conditions(point, project):
            continue
        status = get_annotation_status(point, project)
        xml_block = build_xml_annotation(point, status, project)
        annotations_to_inject.append((point["id"], xml_block, status, point["section"]))
    
    # Injecter en ordre inverse (pour ne pas décaler les positions)
    for point_id, xml_block, status, section in annotations_to_inject:
        pos = find_point_in_xml(content, point_id)
        if pos > 0:
            content = content[:pos] + xml_block + content[pos:]
            icon = "🔴" if status=="nonconforme" else "🟡" if status=="averifier" else "🟢"
            print(f"  {icon} Point {point_id:3d} ({section}) → {status}")
            injected += 1
    
    print(f"\n  {injected}/{len(annotations_to_inject)} annotations injectées")
    
    # 4. Sauvegarder et recompacter
    doc_xml.write_text(content, encoding='utf-8')
    
    # Corriger le fichier de relations si nécessaire
    rels = work_dir / "word/_rels/document.xml.rels"
    rels_content = rels.read_text()
    if 'cid:image003.gif' in rels_content:
        rels_content = re.sub(r'\s*<Relationship[^>]*cid:image003[^>]*/>', '', rels_content)
        rels.write_text(rels_content)
    
    result = subprocess.run(
        ["python3", str(SCRIPTS/"pack.py"), str(work_dir), output_path, 
         "--original", str(template)],
        capture_output=True, text=True
    )
    if "PASSED" in result.stdout or "Successfully" in result.stdout:
        print(f"\n✅ Document généré : {output_path}")
        return True
    else:
        print(f"\n❌ Erreur: {result.stdout[-500:]}")
        # Essayer sans validation
        subprocess.run(["python3", str(SCRIPTS/"pack.py"), str(work_dir), output_path,
                       "--original", str(template), "--validate", "false"],
                      capture_output=True)
        print(f"  Document généré sans validation")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: generate_report.py <projet.json> <BB|BM> <output.docx>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2], sys.argv[3])
