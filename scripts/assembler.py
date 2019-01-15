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
from z80codegen import *
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
		for i in range(0,len(src)):											# and now do stuff.
			if src[i].startswith("defproc"):								# defproc<name>(
				procName = src[i][7:]										# get name
				if procName in self.globals:								# check duplicates
					raise AssemblerException("Duplicate Procedure "+procName[:-1])
				self.globals[procName] = self.codeGen.getAddress()			# define as here.
			else:
				if i > 0:
					self.compileBody(src[i])								# otherwise do the body.
				else:
					AssemblerException.LINE += src[i].count("~")			# preliminary lines
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
	#
	#		Compile procedure body
	#
	def compileBody(self,body):
		body = [x for x in body.split(":") if x != ""]						# split into bits
		if body[0][-1] != ")":												# first is param list.
			raise CompilerException("Parameter syntax")
		params = [x for x in body[0][:-1].split(",") if x != ""]			# get the param list
		for p in range(0,len(params)):										# code to store registers
			if re.match("^\@\d+$",params[p]) is None:						# in parameters.
				raise CompilerException("Bad parameter "+params[p])
			self.codeGen.storeParamRegister(p,int(params[p][1:]))
		self.structStack = [ ["marker"]]									# structure stack.
		for cmd in body[1:]:												# for the rest
			if cmd == "~":													# line marker.
				AssemblerException.LINE += 1
			else:
				self.compileCommand(cmd)
		if len(self.structStack) != 1:										# check all closed.
			raise AssemblerException("Unclosed structure")
	#
	#		Compile a single command.
	#
	def compileCommand(self,cmd):
		print("\t==== "+cmd+" ====")
		#
		if cmd == "endproc":												# endproc command
			self.codeGen.returnSubroutine()
			return
		#
		if cmd.startswith("while(") or cmd.startswith("if("):				# IF/WHILE
			m = re.match("^(\w+)\((.*)([\#\=\<])0\)$",cmd)					# decode it
			if m is None:
				raise AssemblerException("Syntax Error in structure")
			test = { "#":"z","=":"nz","<":"p" }[m.group(3)]					# test is *fail*
			info = [ m.group(1),self.codeGen.getAddress(),test ]
			self.compileExpression(m.group(2))								# test.
			info.append(self.codeGen.getAddress())							# add test position.
			self.structStack.append(info)									# add to stack.
			self.codeGen.jumpInstruction(test,self.codeGen.getAddress()) 	# incomplete branch
			return
		#
		if cmd == "endwhile" or cmd == "endif":								# ENDIF/ENDWHILE
			info = self.structStack.pop()									# get info
			if info[0] != cmd[3:]:											# not mixed up ?
				raise AssemblerException(cmd+" without "+cmd[3:])
			if cmd == "endwhile":											# while, jump to top
				self.codeGen.jumpInstruction("",info[1])
			self.codeGen.jumpInstruction(info[2],self.codeGen.getAddress(),info[3])
			return
		#
		m = re.match("^("+self.rxIdentifier+"\()(.*?)\)$",cmd)				# procedure invocation.
		if m is not None:
			if m.group(1) not in self.globals:								# call exists ?
				raise AssemblerException("Unknown procedure "+m.group(1)[:-1])
			params = [x for x in m.group(2).split(",") if x != ""]			# parameters
			for i in range(0,len(params)):									# work through them
				m2 = re.match("^(\@?)(\d+)$",params[i])						# check syntax
				if m2 is None:
					raise AssemblerException("Bad parameter "+params[i])
																			# code to load to temp reg
				self.codeGen.loadParamRegister(i,m2.group(1) == "",int(m2.group(2)))
			self.codeGen.callSubroutine(self.globals[m.group(1)])			# caller code.
			return		
		#
		self.compileExpression(cmd)											# compile as expression.
	#
	#		Compile an expression.
	#		
	def compileExpression(self,expr):
		expr = [x for x in re.split("(\@?\d+)",expr) if x != ""]			# split round terms
		pendingOp = None													# No operator in progress
		for x in expr:														# work through.
			m = re.match("^(\@?)(\d+)$",x)									# is it nnnn or @nnnn
			if m is not None:
				if pendingOp is not None:									# Operator, do it.
					self.codeGen.binaryOperation(pendingOp,m.group(1) == "",int(m.group(2)))
				else:														# No Op, load first value
					self.codeGen.loadDirect(m.group(1) == "",int(m.group(2)))
				pendingOp = None											# No pending operator
			else:
				if "+-*/%&|^>!".find(x) < 0:								# check its a known operator
					raise AssemblerException("Can't recognise "+x+" in expression")
				pendingOp = x												# mark as pending.

if __name__ == "__main__":
	src = """
	defproc demo(p1,p2)
		p1!0+p2>$g3:"hello"+1>@a:"demo">b				// a comment
	endproc

	defproc d2()
		demo(1,3):
		+$c1.4>@$h2
	endproc

	defproc d3()
		if ($h2=0):c+1>@c:endif
		while ($h2#0):c+1>@c:endwhile
		d2(a,b,c,d)
	endproc
	""".split("\n")
	#cg = DemoCodeGenerator()
	cg = Z80CodeGenerator()
	aw = AssemblerWorker(cg)		
	aw.assemble(src)
	print(aw.globals)
	#aw.codeGen.image.save()
