# ***************************************************************************************
# ***************************************************************************************
#
#		Name : 		democodegen.py
#		Author :	Paul Robson (paul@robsons.org.uk)
#		Date : 		15th January 2019
#		Purpose :	Dummy Code Generator class
#
# ***************************************************************************************
# ***************************************************************************************

# ***************************************************************************************
#					This is a code generator for an idealised CPU
# ***************************************************************************************

class DemoCodeGenerator(object):
	def __init__(self):
		self.pc = 0x1000
		self.ops = { "+":"add","-":"sub","*":"mul","/":"div","%":"mod","&":"and","|":"ora","^":"xor" }
	#
	#		Get current address
	#
	def getAddress(self):
		return self.pc
	#
	#		Get word size
	#
	def getWordSize(self):
		return 2
	#
	#		Load a constant or variable into the accumulator.
	#
	def loadDirect(self,isConstant,value):
		src = ("#${0:04x}" if isConstant else "(${0:04x})").format(value)
		print("${0:06x}  lda   {1}".format(self.pc,src))
		self.pc += 1
	#
	#		Do a binary operation on a constant or variable on the accumulator
	#
	def binaryOperation(self,operator,isConstant,value):
		if operator == "!" or operator == "?":
			self.binaryOperation("+",isConstant,value)
			print("${0:06x}  lda.{1} [a]".format(self.pc,"b" if operator == "?" else "w"))
			self.pc += 1
		else:					
			src = ("#${0:04x}" if isConstant else "(${0:04x})").format(value)
			print("${0:06x}  {1}   {2}".format(self.pc,self.ops[operator],src))
			self.pc += 1
	#
	#	Compile a loop instruction. Test are z, nz, p or "" (unconditional). The compilation
	#	address can be overridden to patch forward jumps.
	#
	def jumpInstruction(self,test,target,override = None):
		if override is None:
			override = self.pc
			self.pc += 1
		print("${0:06x}  jmp   {1}${2:06x}".format(override,test+"," if test != "" else "",target))
	#
	#		Allocate count bytes of meory, default is word size
	#
	def allocVar(self,name = None):
		addr = self.pc
		self.pc += self.getWordSize()
		print("${0:06x}  ds    ${1:04x} ; {2}".format(addr,count,"" if name is None else name))
		return addr
	#
	#		Create a string constant (done outside procedures)
	#
	def createStringConstant(self,string):
		sAddr = self.pc
		print("${0:06x}  db    \"{1}\",0".format(self.pc,string))
		self.pc += len(string)+1
		return sAddr
	#
	#		Call a subroutine
	#
	def callSubroutine(self,address):
		print("${0:06x}  jsr   ${1:06x}".format(self.pc,address))
		self.pc += 1
	#
	#		Return from subroutine.
	#
	def returnSubroutine(self):
		print("${0:06x}  rts".format(self.pc))
		self.pc += 1

