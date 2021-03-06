import sys
import suds
import logging
import sudspatch
from suds.transport.http import HttpAuthenticated
from suds.transport import Request

class API:
	
	url = "https://api.profitbricks.com/1.2/wsdl"
	debug = False
	requestId = None
	datacenters = []
	
	def __init__(self, username, password, debug = False):
		self.debug = debug
		if debug:
			logging.getLogger("suds.server").setLevel(logging.DEBUG)
			logging.getLogger("suds.client").setLevel(logging.DEBUG)
			logging.getLogger("suds.transport").setLevel(logging.DEBUG)
		else:
			logging.getLogger('suds.client').setLevel(logging.CRITICAL) # hide soap faults
		
		try:
			self.client = suds.client.Client(url = self.url, username = username, password = password)
		except suds.transport.TransportError as (err):
			raise Exception("Authentication error: Invalid username or password." if err.httpcode == 401 else "Unknown initialization error: %s" % str(err))
	
	# Calls the func() function using SOAP and the given arguments list (must always be an array)
	def _call(self, func, args):
		if (self.debug):
			print "# Calling %s %s" % (func, args)
		try:
			method = getattr(self.client.service, func)
			result = method(*args)
			if self.requestId is None:
				if "requestId" in result:
					self.requestId = result["requestId"]
				else:
					self.requestId = "(no info)"
			if func == "getAllDataCenters":
				API.datacenters = result
			return result
		except suds.WebFault as (err):
			raise Exception(str(err))
		except suds.transport.TransportError as (err):
			raise Exception("Authentication error: Invalid username or password." if err.httpcode == 401 else "Transport error: %s" % str(err))
	
	# Returns the userArgs hash, but replaces the keys with the values found in translation and only the ones found in translation
	# eg, _parseArgs({"a": 10, "b": 20, "c": 30}, {"a": "a", "b": "B"}) => {"a": 10, "B": 20}
	def _parseArgs(self, userArgs, translation):
		args = {}
		for i in translation:
			if i.lower() in userArgs:
				args[translation[i]] = userArgs[i.lower()]
		return args
	
	def getAllDataCenters(self):
		return self._call("getAllDataCenters", [])
	
	def getDataCenter(self, id):
		return self._call("getDataCenter", [id])
	
	def getServer(self, id):
		return self._call("getServer", [id])
	
	def createDataCenter(self, name, region):
		return self._call("createDataCenter", [name, region.upper()])
	
	def getDataCenterState(self, id):
		return self._call("getDataCenterState", [id])
	
	def updateDataCenter(self, userArgs):
		args = self._parseArgs(userArgs, {"dcid": "dataCenterId", "name": "dataCenterName"})
		return self._call("updateDataCenter", [args])
	
	def clearDataCenter(self, id):
		return self._call("clearDataCenter", [id])
	
	def deleteDataCenter(self, id):
		return self._call("deleteDataCenter", [id])
	
	def createServer(self, userArgs):
		args = self._parseArgs(userArgs, {"cores": "cores", "ram": "ram", "bootFromStorageId": "bootFromStorageId", "bootFromImageId": "bootFromImageId", "lanId": "lanId", "dcid": "dataCenterId", "name": "serverName"})
		if "ostype" in userArgs:
			args["osType"] = userArgs["ostype"].upper()
		if "internetaccess" in userArgs:
			args["internetAccess"] = (userArgs["internetaccess"][:1].lower() == "y")
		if "zone" in userArgs:
			args["availabilityZone"] = userArgs["zone"].upper()
		return self._call("createServer", [args])
	
	def rebootServer(self, id):
		return self._call("rebootServer", [id])
	
	def updateServer(self, userArgs):
		args = self._parseArgs(userArgs, {"srvid": "serverId", "name": "serverName", "cores": "cores", "ram": "ram", "bootFromImageId": "bootFromImageId", "bootFromStorageId": "bootFromStorageId"})
		if "ostype" in userArgs:
			args["osType"] = userArgs["ostype"].upper()
		if "zone" in userArgs:
			args["availabilityZone"] = userArgs["zone"].upper()
		return self._call("updateServer", [args])
	
	def deleteServer(self, id):
		return self._call("deleteServer", [id])
	
	def createStorage(self, userArgs):
		args = self._parseArgs(userArgs, {"dcid": "dataCenterId", "size": "size", "name": "storageName", "imgid": "mountImageId"})
		return self._call("createStorage", [args])
	
	def getStorage(self, id):
		return self._call("getStorage", [id])
	
	def connectStorageToServer(self, userArgs):
		args = self._parseArgs(userArgs, {"stoid": "storageId", "srvid": "serverId", "devnum": "deviceNumber"})
		args["busType"] = (args["bus"] if "bus" in userArgs else "VIRTIO").upper()
		return self._call("connectStorageToServer", [args])
	
	def disconnectStorageFromServer(self, stoId, srvId):
		return self._call("disconnectStorageFromServer", [stoId, srvId])
	
	def updateStorage(self, userArgs):
		args = self._parseArgs(userArgs, {"stoid": "storageId", "name": "storageName", "size": "size"})
		return self._call("updateStorage", [args])
	
	def deleteStorage(self, id):
		return self._call("deleteStorage", [id])
	
	def createLoadBalancer(self, userArgs):
		args = self._parseArgs(userArgs, {"dcid": "dataCenterId", "name": "loadBalancerName", "ip": "ip", "lanid": "lanId"})
		if "algo" in userArgs:
			args["loadBalancerAlgorithm"] = userArgs["algo"].upper()
		if "srvid" in userArgs:
			args["serverIds"] = userArgs["srvid"].split(",")
		result = self._call("createLoadBalancer", [args])
		return result.loadBalancerId
	
	def getLoadBalancer(self, id):
		return self._call("getLoadBalancer", [id])
	
	def updateLoadBalancer(self, userArgs):
		args = self._parseArgs(userArgs, {"bid": "loadBalancerId", "name": "loadBalancerName", "ip": "ip"})
		if "algo" in userArgs:
			args["loadBalancerAlgorithm"] = userArgs["algo"].upper()
		return self._call("updateLoadBalancer", [args])
	
	def registerServersOnLoadBalancer(self, srvids, bid):
		return self._call("registerServersOnLoadBalancer", [srvids, bid])
	
	def deregisterServersOnLoadBalancer(self, srvids, bid):
		return self._call("deregisterServersOnLoadBalancer", [srvids, bid])
	
	def activateLoadBalancingOnServers(self, srvids, bid):
		return self._call("activateLoadBalancingOnServers", [srvids, bid])
	
	def deactivateLoadBalancingOnServers(self, srvids, bid):
		return self._call("deactivateLoadBalancingOnServers", [srvids, bid])
	
	def deleteLoadBalancer(self, id):
		return self._call("deleteLoadBalancer", [id])
	
	def addRomDriveToServer(self, userArgs):
		args = self._parseArgs(userArgs, {"imgid": "imageId", "srvid": "serverId", "devnum": "deviceNumber"})
		return self._call("addRomDriveToServer", [args])
	
	def removeRomDriveFromServer(self, id, srvid):
		return self._call("addRomDriveToServer", [id, srvid])
	
	def setImageOsType(self, imgid, ostype):
		return self._call("setImageOsType", [imgid, ostype])
	
	def getImage(self, id):
		return self._call("getImage", [id])
	
	def getAllImages(self):
		return self._call("getAllImages", [])
	
	def deleteImage(self, id):
		return self._call("deleteImage", [id])
	
	def createNIC(self, userArgs):
		args = self._parseArgs(userArgs, {"srvid": "serverId", "lanid": "lanId", "name": "nicName", "ip": "ip"})
		return self._call("createNic", [args])
	
	def getNIC(self, id):
		return self._call("getNic", [id])
	
	def setInternetAccess(self, dcid, lanid, internetAccess):
		return self._call("setInternetAccess", [dcid, lanid, internetAccess])
	
	def updateNIC(self, userArgs):
		args = self._parseArgs(userArgs, {"nicid": "nicId", "lanid": "lanId", "name": "nicName"})
		if "ip" in userArgs:
			args["ip"] = (userArgs["ip"] if userArgs["ip"].lower() != "reset" else "")
		return self._call("updateNic", [args])
	
	def deleteNIC(self, id):
		return self._call("deleteNic", [id])
	
	def reservePublicIPBlock(self, size, region):
		return self._call("reservePublicIpBlock", [size, region.upper()])
	
	def addPublicIPToNIC(self, ip, nicId):
		return self._call("addPublicIpToNic", [ip, nicId])
	
	def getAllPublicIPBlocks(self):
		result = self._call("getAllPublicIpBlocks", [])
		return result
	
	def removePublicIPFromNIC(self, ip, nicId):
		return self._call("removePublicIpFromNic", [ip, nicId])
	
	def releasePublicIPBlock(self, id):
		return self._call("releasePublicIpBlock", [id])
	
	def _parseFirewallRule(self, userRule):
		rule = self._parseArgs(userRule, {"smac": "sourceMac", "sip": "sourceIp", "dip": "targetIp", "icmptype": "icmpType", "icmpcode": "icmpCode"})
		if "proto" in userRule:
			rule["protocol"] = userRule["proto"].upper()
		if "port" in userRule:
			ports = userRule["port"].split("-")
			rule["portRangeStart"] = ports[0]
			rule["portRangeEnd"] = ports[len(ports) - 1]
		return rule
	
	def addFirewallRuleToNic(self, id, userRule):
		rule = self._parseFirewallRule(userRule)
		return self._call("addFirewallRulesToNic", [[rule], id])

	def addFirewallRuleToLoadBalancer(self, id, userRule):
		rule = self._parseFirewallRule(userRule)
		return self._call("addFirewallRulesToLoadBalancer", [[rule], id])

	def activateFirewall(self, id):
		return self._call("activateFirewalls", [id])

	def deactivateFirewall(self, id):
		return self._call("deactivateFirewalls", [id])

	def deleteFirewall(self, id):
		return self._call("deleteFirewalls", [id])
