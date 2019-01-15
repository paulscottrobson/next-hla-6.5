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
	#
	#		Assemble an array of strings.
	#
	def assemble(self,src):
		#
		AssemblerException.LINE = 0											# reset line ref.
		src = self.preProcess(src)											# pre-process
		print(src)
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

if __name__ == "__main__":
	src = """
		"hello"+1>a:"demo">b				// a comment
	""".split("\n")
	aw = AssemblerWorker(DemoCodeGenerator())		
	aw.assemble(src)
	print(aw.globals)
	#aw.codeGen.image.save()
