#!/usr/bin/python
from __future__ import print_function
import argparse
import re
from Collapser import Collapser
from BaseEval import BaseEvalInput
from aritheval import EAConstMul, EAConstDiv, EASplit, EAZerop, EAAdd, EAMul, EADiv

class ArithConvert(Collapser):
	def __init__(self):
		Collapser.__init__(self)
		self.gates = {}
		self.outputs = set()

		parser = argparse.ArgumentParser(description='Evaluate circuit')
		parser.add_argument('circuitfile', metavar='<circuitfile>',
			help='the circuit file')
		parser.add_argument('infile', metavar='<infile>',
			help='the input I/O file')

		args = parser.parse_args()
		self.parse(args.circuitfile)
		self.gen_constraints()
		self.load_inputs(args.infile)
		self.evaluate()
		self.fill_gaps()
		self.gen_write_wires()


	def sub_parse(self, verb, in_a, out_a):
		if (verb=='split'):
			assert(False)
		elif (verb=="add"):
			self.add_gate(self.unique(out_a), EAAdd(in_a))
		elif (verb=="mul"):
			self.add_gate(self.unique(out_a), EAMul(in_a))
		elif (verb=="div"):
			self.add_gate(self.unique(out_a), EADiv(in_a))
		elif (verb.startswith("const-mul-")):
			if (verb[10:14]=="neg-"):
				sign = -1
				value = verb[14:]
			else:
				sign = 1
				value = verb[10:]
			const = int(value, 16) * sign
			self.add_gate(self.unique(out_a), EAConstMul(const, self.unique(in_a)))
		elif (verb=="zerop"):
			self.add_gate(out_a[0], EAZerop(self.unique(in_a)))
			self.add_gate(out_a[1], EAZerop(self.unique(in_a)))
		elif (verb.startswith("const-div-")):
			if (verb[10:14]=="neg-"):
				sign = -1
				value = verb[14:]
			else:
				sign = 1
				value = verb[10:]
			const = int(value, 16) * sign
			self.add_gate(self.unique(out_a), EAConstDiv(const, self.unique(in_a)))
		else:
			assert(False)

	def unique(self, array):
		assert(len(array)==1)
		return array[0]

	def parse_line(self, line):
		verbsplit = filter(lambda t: t != '', line.split(' ', 1))
		if (len(verbsplit)<1):
			# blank line.
			return
		(verb,rest) = verbsplit
		if (verb=='total'):
			if (self.total_wires!=None):
				raise Exception("Duplicate total line")
			self.total_wires = int(rest)
		elif (verb=='input'):
			wire_id = int(rest)
			self.add_gate(wire_id, BaseEvalInput(wire_id))
		elif (verb=='output'):
			self.outputs.add(int(rest))
		else:
			(in_a,out_a) = self.parse_io_list(rest)
			self.sub_parse(verb, in_a, out_a)


	def parse(self, arith_fn):
		self.total_wires = None	# not so important now that every wire is represented
		ifp = open(arith_fn, "r")
		for line in ifp.readlines():
			line = line.rstrip()
			noncomment = line.split("#")[0]
			self.parse_line(noncomment)
		ifp.close()

		# verify a couple properties
		# all the outputs exist
		for w in self.outputs:
			assert(w in self.gates)

		# no wires number greater than the total_wires
		wire_ids = self.gates.keys()
		wire_ids.sort()
		max_wire = wire_ids[-1]
		assert(max_wire+1==self.total_wires)

		# all wires should have been labeled.
		for wire_id in range(self.total_wires):
			if (wire_id not in self.gates):
				raise Exception("%s not in gates" % wire_id)

	def evaluate(self):
		for wire_id in self.output_ids:
			self.collapse_tree(wire_id)

	def load_inputs(self, in_fn):
		self.inputs = {}
		ifp = open(in_fn, "r")
		for line in ifp.readlines():
			(wire_id_s,value_s) = line.split(' ')
			wire_id = int(wire_id_s)
			value = int(value_s, 16)
			self.inputs[wire_id] = value
		ifp.close()

		for (wire_id,gate) in self.gates.items():
			if (isinstance(gate, BaseEvalInput)):
				if (wire_id not in self.inputs):
					raise Exception("No value assigned to Input %s" % wire_id)


	def add_gate(self, wire_id, gate):
		if (wire_id in self.gates):
			raise Exception("duplicate wire %s" % wire_id)
		self.gates[wire_id] = gate


	def parse_io_list(self, io_str):
		mo = re.compile("in +([0-9]*) +<([0-9 ]*)> +out +([0-9]*) +<([0-9 ]*)>").search(io_str)
		if (mo==None):
			raise Exception("Not an io list: '%s'" % io_str)
		things = mo.groups(0)
		in_l = int(things[0])
		in_a = map(int, things[1].split())
		assert(len(in_a)==in_l)
		out_l = int(things[2])
		out_a = map(int, things[3].split())
		assert(len(out_a)==out_l)
		return (in_a, out_a)

	def fill_gaps(self):
		wire_ids = self.table.keys()	# Note peek into superclass' member. :v(
		wire_ids.sort()
		max_wire_id = wire_ids[-1]
		full_set = set(range(0, max_wire_id))
		missing_wire_ids = list(full_set - set(wire_ids))
		missing_wire_ids.sort()
		for wire_id in missing_wire_ids:
			self.collapse_tree(wire_id)

	def get_input(self, wire):
		return self.inputs[wire]

	def get_dependencies(self, wire):
		deps = self.gates[wire].inputs()
		if (len(deps)>0 and not (max(deps) < wire)):
			raise Exception("arith file doesn't flow monotonically: deps %s come after wire %s" % (deps, wire))
		return deps

	def collapse_impl(self, wire):
		return self.gates[wire].eval(self)

	def gen_constraints(self):
		self.output_ids = list(self.outputs)
		self.output_ids.sort()
		f = open("arith_converted", "w")
		f.write("input %d\n" % self.total_wires)
		f.write("out_start %d\n" % self.output_ids[0])
		for outid, gate in self.gates.items():
			# EAConstMul, EAConstDiv, EASplit, EAZerop, EAAdd, EAMul, EADiv
			if isinstance(gate, EAAdd):
				f.write("add %d %d %d\n" % (gate.wire_list[0], gate.wire_list[1], outid))
			elif isinstance(gate, EAMul): 
				f.write("mul %d %d %d\n" % (gate.wire_list[0], gate.wire_list[1], outid))
			elif isinstance(gate, EADiv):
				f.write("div %d %d %d\n" % (outid, gate.wire_list[1], gate.wire_list[0]))
			elif isinstance(gate, EAConstMul):
				f.write("constmul %d %d %d\n" % (gate.wire_id, gate.const, outid))
			elif isinstance(gate, EAConstDiv):
				pass
				# print("pb.add_r1cs_constraint(r1cs_constraint<FieldT>(var_%d, %d, var_%d));" % (outid, gate.const, gate.wire_id))
			elif isinstance(gate, BaseEvalInput):
				pass
			else:
				assert(False)
	def gen_write_wires(self):
		f = open("arith_wires", "w")
		wire_ids = self.table.keys()	# Note peek into superclass' member. :v(
		wire_ids.sort()
		next_wire_id = 0
		for wire_id in wire_ids:
			if wire_id > next_wire_id:
				for i in range(next_wire_id, wire_id):
					assert(False)
			val = int(self.lookup(wire_id))
			f.write("%d %s\n" % (wire_id, hex(val).replace("L", "")))
			next_wire_id = wire_id+1


if __name__ == '__main__':
	ArithConvert()
