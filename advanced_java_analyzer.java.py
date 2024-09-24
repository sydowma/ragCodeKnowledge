import re


class AdvancedJavaAnalyzer:
    def __init__(self, code):
        self.code = code
        self.classes = {}
        self.interfaces = {}
        self.relationships = []

    def analyze(self):
        # 移除注释
        self.code = re.sub(r'(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)|(//.*)', '', self.code)

        # 分析类和接口
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

        # 分析方法和字段
        for class_name, class_info in self.classes.items():
            class_code = self.extract_class_code(class_name)
            self.analyze_members(class_name, class_code)

    def extract_class_code(self, class_name):
        class_pattern = rf'class\s+{class_name}.*?{{(.*?)}}'
        match = re.search(class_pattern, self.code, re.DOTALL)
        return match.group(1) if match else ''

    def analyze_members(self, class_name, class_code):
        # 分析方法
        method_pattern = r'(public|private|protected)?\s+(\w+)\s+(\w+)\s*\([^)]*\)\s*{'
        for match in re.finditer(method_pattern, class_code):
            method_name = match.group(3)
            self.classes[class_name]['methods'].append(method_name)

        # 分析字段
        field_pattern = r'(public|private|protected)?\s+(\w+)\s+(\w+)\s*;'
        for match in re.finditer(field_pattern, class_code):
            field_type = match.group(2)
            field_name = match.group(3)
            self.classes[class_name]['fields'].append((field_type, field_name))
            if field_type in self.classes:
                self.relationships.append((class_name, field_type, 'associates'))

    def generate_mermaid(self):
        mermaid_code = ["```mermaid", "classDiagram"]

        # 添加类和接口
        for name, info in {**self.classes, **self.interfaces}.items():
            mermaid_code.append(f"    class {name} {{")
            for field_type, field_name in info.get('fields', []):
                mermaid_code.append(f"        {field_type} {field_name}")
            for method in info.get('methods', []):
                mermaid_code.append(f"        {method}()")
            mermaid_code.append("    }")

        # 添加关系
        for source, target, relation in self.relationships:
            if relation == 'extends':
                mermaid_code.append(f"    {source} --|> {target}")
            elif relation == 'implements':
                mermaid_code.append(f"    {source} ..|> {target}")
            elif relation == 'associates':
                mermaid_code.append(f"    {source} --> {target}")

        mermaid_code.append("```")
        return "\n".join(mermaid_code)


def analyze_java_code(code):
    analyzer = AdvancedJavaAnalyzer(code)
    analyzer.analyze()
    return analyzer.generate_mermaid()


# 示例使用
sample_java_code = """
public abstract class Animal {
    protected String name;
    public abstract void makeSound();
}

public class Dog extends Animal {
    private Tail tail;
    public void makeSound() {
        System.out.println("Woof!");
    }
    public void fetch() {
        System.out.println("Fetching...");
    }
}

public class Cat extends Animal implements Playful {
    public void makeSound() {
        System.out.println("Meow!");
    }
    public void play() {
        System.out.println("Cat is playing");
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
"""

mermaid_diagram = analyze_java_code(sample_java_code)
print(mermaid_diagram)