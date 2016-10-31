'''
Example of Linda Proxy in Python

 Licensed with Apache Public License
 by AAAI Research Group
 Department of Information Engineering and Computer Science and Mathematics
 University of L'Aquila, ITALY
 http://www.disim.univaq.it

'''

import lindaproxy as lp

# Main

L = lp.LindaProxy(host='10.0.40.173')
L.send_message('agent1', 'go')