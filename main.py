'''
Example of Linda Proxy in Python

 Licensed with Apache Public License
 by AAAI Research Group
 Department of Information Engineering and Computer Science and Mathematics
 University of L'Aquila, ITALY
 http://www.disim.univaq.it

'''

import DALI.LindaProxy.lindaproxy as lp
import time
# Main

L = lp.LindaProxy(host='127.0.0.1')
L.send_message('agent1', 'go')
L.start()
