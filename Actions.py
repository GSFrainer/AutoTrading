class Orders:

    def __init__(self, request_client):
        self.request_client = request_client

    def newAlert(self, stop=0, take=0):
        print('- New Order Alert:')
        print('- - Stop: '+str(stop))
        print('- - Take: '+str(take))