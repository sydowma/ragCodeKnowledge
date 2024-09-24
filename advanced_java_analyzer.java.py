import os
import re
from collections import defaultdict

# generate class diagram from Java code
class ProjectJavaAnalyzer:
    def __init__(self):
        self.classes = {}
        self.interfaces = {}
        self.relationships = []
        self.imports = {}
        self.method_calls = defaultdict(list)
        self.package_structure = defaultdict(list)
        self.common_classes = {'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean',
                               'BigDecimal', 'BigInteger', 'List', 'ArrayList', 'LinkedList',
                               'Set', 'HashSet', 'TreeSet', 'Map', 'HashMap', 'TreeMap',
                               'Queue', 'Deque', 'Stack', 'Vector'}

    def analyze_project(self, directory):
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    self.analyze_file(code, file_path)

    def analyze_file(self, code, file_path):
        self.current_file = file_path
        self.parse_package(code)
        self.parse_imports(code)
        self.remove_comments(code)
        self.parse_classes_and_interfaces(code)
        self.analyze_method_calls(code)

    def parse_package(self, code):
        package_match = re.search(r'package\s+([\w.]+);', code)
        if package_match:
            package = package_match.group(1)
            class_name = os.path.basename(self.current_file)[:-5]  # Remove .java
            self.package_structure[package].append(class_name)

    def parse_imports(self, code):
        import_pattern = r'import\s+([\w.]+)\s*;'
        for match in re.finditer(import_pattern, code):
            full_path = match.group(1)
            class_name = full_path.split('.')[-1]
            if class_name not in self.common_classes:
                self.imports[class_name] = full_path

    def remove_comments(self, code):
        return re.sub(r'(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)|(//.*)', '', code)

    def parse_classes_and_interfaces(self, code):
        class_pattern = r'(public\s+)?(abstract\s+)?(class|interface)\s+(\w+)(\s+extends\s+(\w+))?(\s+implements\s+([\w,\s]+))?'
        for match in re.finditer(class_pattern, code):
            name = match.group(4)
            kind = match.group(3)
            parent = match.group(6)
            implements = match.group(8)

            if kind == 'class':
                if name not in self.common_classes:
                    self.classes[name] = {'methods': [], 'fields': []}
                    if parent and parent not in self.common_classes:
                        self.relationships.append((name, parent, 'extends'))
                    if implements:
                        for interface in implements.split(','):
                            interface = interface.strip()
                            if interface not in self.common_classes:
                                self.relationships.append((name, interface, 'implements'))
            else:
                self.interfaces[name] = {'methods': []}

            class_code = self.extract_class_code(name, code)
            self.analyze_members(name, class_code)

    def extract_class_code(self, class_name, code):
        class_pattern = rf'class\s+{class_name}.*?{{(.*?)}}'
        match = re.search(class_pattern, code, re.DOTALL)
        return match.group(1) if match else ''

    def analyze_members(self, class_name, class_code):
        method_pattern = r'(public|private|protected)?\s+(\w+)\s+(\w+)\s*\([^)]*\)'
        field_pattern = r'(public|private|protected)?\s+(\w+)\s+(\w+)\s*;'

        for match in re.finditer(method_pattern, class_code):
            method_name = match.group(3)
            self.classes[class_name]['methods'].append(method_name)

        for match in re.finditer(field_pattern, class_code):
            field_type = match.group(2)
            field_name = match.group(3)
            self.classes[class_name]['fields'].append((field_type, field_name))
            if field_type in self.classes or field_type in self.imports:
                self.relationships.append((class_name, field_type, 'associates'))

    def analyze_method_body(self, class_name, method_name, method_body):
        method_call_pattern = r'(\w+)\.(\w+)\('
        for match in re.finditer(method_call_pattern, method_body):
            object_name = match.group(1)
            called_method = match.group(2)
            self.method_calls[f"{class_name}.{method_name}"].append(f"{object_name}.{called_method}")

    def analyze_method_calls(self, code):
        for caller, callees in self.method_calls.items():
            caller_class = caller.split('.')[0]
            for callee in callees:
                callee_parts = callee.split('.')
                if len(callee_parts) == 2:
                    object_name, method_name = callee_parts
                    if object_name in self.classes or object_name in self.imports:
                        self.relationships.append((caller_class, object_name, 'uses'))

    def generate_mermaid(self):
        mermaid_code = ["```mermaid", "classDiagram"]

        # Add classes and interfaces
        for name, info in {**self.classes, **self.interfaces}.items():
            mermaid_code.append(f"    class {name} {{")
            for field_type, field_name in info.get('fields', []):
                mermaid_code.append(f"        {field_type} {field_name}")
            for method in info.get('methods', []):
                mermaid_code.append(f"        {method}()")
            mermaid_code.append("    }")

        # Add relationships
        for source, target, relation in self.relationships:
            if relation == 'extends':
                mermaid_code.append(f"    {source} --|> {target}")
            elif relation == 'implements':
                mermaid_code.append(f"    {source} ..|> {target}")
            elif relation == 'associates':
                mermaid_code.append(f"    {source} --> {target}")
            elif relation == 'uses':
                mermaid_code.append(f"    {source} ..> {target} : uses")

        mermaid_code.append("```")
        return "\n".join(mermaid_code)

def analyze_java_project(directory):
    analyzer = ProjectJavaAnalyzer()
    analyzer.analyze_project(directory)
    return analyzer.generate_mermaid()

# 示例使用
project_directory = ''
print(project_directory)
mermaid_diagram = analyze_java_project(project_directory)
print(mermaid_diagram)