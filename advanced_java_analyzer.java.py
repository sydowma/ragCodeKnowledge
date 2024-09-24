import re
from collections import defaultdict


class ComprehensiveJavaAnalyzer:
    def __init__(self, code):
        self.code = code
        self.classes = {}
        self.interfaces = {}
        self.relationships = []
        self.imports = {}
        self.method_calls = defaultdict(list)

    def analyze(self):
        self.parse_imports()
        self.remove_comments()
        self.parse_classes_and_interfaces()
        self.analyze_method_calls()

    def parse_imports(self):
        import_pattern = r'import\s+([\w.]+)\s*;'
        for match in re.finditer(import_pattern, self.code):
            full_path = match.group(1)
            class_name = full_path.split('.')[-1]
            self.imports[class_name] = full_path

    def remove_comments(self):
        self.code = re.sub(r'(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)|(//.*)', '', self.code)

    def parse_classes_and_interfaces(self):
        class_pattern = r'(public\s+)?(abstract\s+)?(class|interface)\s+(\w+)(\s+extends\s+(\w+))?(\s+implements\s+([\w,\s]+))?'
        for match in re.finditer(class_pattern, self.code):
            name = match.group(4)
            kind = match.group(3)
            parent = match.group(6)
            implements = match.group(8)

            if kind == 'class':
                self.classes[name] = {'methods': [], 'fields': []}
                if parent:
                    self.relationships.append((name, parent, 'extends'))
                if implements:
                    for interface in implements.split(','):
                        self.relationships.append((name, interface.strip(), 'implements'))
            else:
                self.interfaces[name] = {'methods': []}

            class_code = self.extract_class_code(name)
            self.analyze_members(name, class_code)

    def extract_class_code(self, class_name):
        class_pattern = rf'class\s+{class_name}.*?{{(.*?)}}'
        match = re.search(class_pattern, self.code, re.DOTALL)
        return match.group(1) if match else ''

    def analyze_members(self, class_name, class_code):
        method_pattern = r'(public|private|protected)?\s+(\w+)\s+(\w+)\s*\([^)]*\)\s*{([^}]*)}'
        field_pattern = r'(public|private|protected)?\s+(\w+)\s+(\w+)\s*;'

        for match in re.finditer(method_pattern, class_code):
            method_name = match.group(3)
            method_body = match.group(4)
            self.classes[class_name]['methods'].append(method_name)
            self.analyze_method_body(class_name, method_name, method_body)

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

    def analyze_method_calls(self):
        for caller, callees in self.method_calls.items():
            caller_class = caller.split('.')[0]
            for callee in callees:
                callee_parts = callee.split('.')
                if len(callee_parts) == 2:
                    object_name, method_name = callee_parts
                    # Check if the object is a known class or imported class
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


def analyze_java_code(code):
    analyzer = ComprehensiveJavaAnalyzer(code)
    analyzer.analyze()
    return analyzer.generate_mermaid()


# 示例使用
sample_java_code = """
import java.util.List;
import com.example.Utility;

public abstract class Animal {
    protected String name;
    public abstract void makeSound();
}

public class Dog extends Animal {
    private Tail tail;
    private Utility utility;

    public void makeSound() {
        System.out.println("Woof!");
    }

    public void fetch() {
        utility.doSomething();
        tail.wag();
    }
}

public class Cat extends Animal implements Playful {
    private List<Toy> toys;

    public void makeSound() {
        System.out.println("Meow!");
    }

    public void play() {
        Toy toy = toys.get(0);
        toy.use();
    }
}

public interface Playful {
    void play();
}

public class Tail {
    private int length;
    public void wag() {
        System.out.println("Tail is wagging");
    }
}

public class Toy {
    public void use() {
        System.out.println("Playing with toy");
    }
}
"""

mermaid_diagram = analyze_java_code(sample_java_code)
print(mermaid_diagram)