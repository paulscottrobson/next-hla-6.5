# ***************************************************************************************
# ***************************************************************************************
#
#		Name : 		assembler.py
#		Author :	Paul Robson (paul@robsons.org.uk)
#		Date : 		15th January 2019
#		Purpose :	Next High Level Assembler, assembler worker.
#
# ***************************************************************************************
# ***************************************************************************************

from democodegen import *
import re

# ***************************************************************************************
#									Exception for HLA
# ***************************************************************************************

class AssemblerException(Exception):
	def __init__(self,message):
		Exception.__init__(self)
		self.message = message
		print(message,AssemblerException.LINE)

# ***************************************************************************************
#									 Worker Object
# ***************************************************************************************

class AssemblerWorker(object):
	def __init__(self,codeGen):
		self.codeGen = codeGen 												# code generator.
		self.globals = {}													# global identifiers.
		self.rxIdentifier = "[\$a-z][a-z0-9\_\.]*"							# identifier rx match
		self.keywords = "if,endif,defproc,endproc,while,endwhile".split(",")# keywords
	#
	#		Assemble an array of strings.
	#
	def assemble(self,src):
		#
		AssemblerException.LINE = 0											# reset line ref.
		src = self.preProcess(src)											# pre-process
		src = (":~:".join(src)).replace(" ","").lower()						# make one string
		src = re.split("(defproc\w+\()",src)								# split into parts
		for i in range(0,len(src)):											# variable proecess
			if not src[i].startswith("defproc"):							# replace variables
				src[i] = self.processVars(src[i])							# with @<address>
		print("\n".join(src))															
	#
	#		Preprocess, and handle quoted text.
	#
	def preProcess(self,src):
		src = [x if x.find("//") < 0 else x[:x.find("//")] for x in src]	# remove comments
		src = [x.replace("\t"," ").strip() for x in src]					# remove tabs and strip
		src = [self.quoteProcess(x) if x.find('"') >= 0 else x for x in src]# remove quoted strings	
		return src
	#
	#		Remove quoted string from a line.
	#
	def quoteProcess(self,l):
		if l.count('"') % 2 != 0:											# check even quotes.
			raise AssemblerException("Imbalanced quotes "+l)
		parts = re.split("(\".*?\")",l)										# split up into qstrings
		parts = [str(self.codeGen.createStringConstant(x[1:-1])) 			# convert "x" to addresses
								if x.startswith('"') else x for x in parts]
		return "".join(parts)												# rebuild line.
	#
	#		Process local/global variables, convert to addresses.
	#
	def processVars(self,code):
		self.locals = {}													# new set of locals
		rxSplit = "("+self.rxIdentifier+"\(?)"								# splitter check proc calls.
		parts = re.split(rxSplit,code)										# split it up.
		idrx = re.compile("^"+self.rxIdentifier+"$")						# matching ID, not call
		parts = [self.createVar(x) if idrx.match(x) else x for x in parts]
		return "".join(parts).replace("@@","")								# restick, fix @var 
	#
	#		Create variable
	#
	def createVar(self,ident):
		if ident in self.keywords:											# keyword
			return ident
		target = self.globals if ident.startswith("$") else self.locals 	# where to look/create
		if ident not in target:												# create if required.
			target[ident] = self.codeGen.allocVar(ident)				
		return "@"+str(target[ident])										# return address

if __name__ == "__main__":
	src = """
	defproc demo(p1,p2)
		p1!0+p2>$g3:"hello"+1>a:"demo">b				// a comment
	endproc
	defproc d2()
		demo(1,3):+$c1.4>@$h2
	endproc
	""".split("\n")
	aw = AssemblerWorker(DemoCodeGenerator())		
	aw.assemble(src)
	print(aw.globals)
	#aw.codeGen.image.save()
