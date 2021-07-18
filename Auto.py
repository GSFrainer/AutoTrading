class Auto:
    meths = {}

    def Auto_func(self):
        print('Auto_func: Ready')
    
    def Exec(self):
        print('Exec')
        self.meths['Auto_func'] = getattr(self, 'Auto_func')
    
    def Exec2(self, s):
        self.meths[s]()

auto = Auto()

#Auto.__dict__['Exec'](auto)
auto.Exec()
auto.Exec2('Auto_func')
