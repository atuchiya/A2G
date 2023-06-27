
class Circuit:
    def __init__(self):
        self.elements = []
        self.nodes = set()

    def add_element(self, element):
        self.elements.append(element)
        self.nodes.update(element.nodes)

class Element:
    def __init__(self, name, nodes):
        self.name = name
        self.nodes = nodes

    def __repr__(self):
        return f"{self.name}: {', '.join(self.nodes)}"
    
class Device(Element):
    def __init__(self, name, nodes, device):
        super().__init__(name, nodes)
        self.device = device

class Resistor(Element):
    def __init__(self, name, nodes, resistance):
        super().__init__(name, nodes)
        self.resistance = resistance

class Capacitor(Element):
    def __init__(self, name, nodes, capacitance):
        super().__init__(name, nodes)
        self.capacitance = capacitance

class Inductor(Element):
    def __init__(self, name, nodes, inductance):
        super().__init__(name, nodes)
        self.inductance = inductance

class VoltageSource(Element):
    def __init__(self, name, nodes, voltage):
        super().__init__(name, nodes)
        self.voltage = voltage

class CurrentSource(Element):
    def __init__(self, name, nodes, current):
        super().__init__(name, nodes)
        self.current = current
