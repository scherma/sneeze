from watchdog.observers import Observer

class InterfaceObserver(Observer):

	def __init__(self):
		super(InterfaceObserver, self).__init__()

		self.interface = str

	def set_interface(interface):
		self.interface = interface
