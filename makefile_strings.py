ncsim_string = """
UVM_VERBOSITY = UVM_MEDIUM
TEST = {0}_test
TB = {0}_tb_top
include	Makefile.srclist

IRUN = irun -uvmhome CDNS-1.2 -incdir $(SRC) \\
	+define+UVM_OBJECT_MUST_HAVE_CONSTRUCTOR -l irun.log \\
	+UVM_VERBOSITY=$(UVM_VERBOSITY) -timescale 1ns/1ns \\
	+UVM_TESTNAME=$(TEST) +UVM_TR_RECORD +UVM_LOG_RECORD \\
	-top $(TB) -ACCESS +rwc -coverage U -covoverwrite \\
	#-gui -simvisargs "-input ./simvision.svcf"

x:	run

run:
	$(IRUN) $(SRCS)

clean:
	rm -rf INCA_libs irun.log waves.shm
"""

vcs_string = """
UVM_VERBOSITY = UVM_MEDIUM
TEST = {0}_test
include Makefile.srclist

VCS =	vcs -sverilog -timescale=1ns/1ns \\
	+acc +vpi -PP \\
	+define+UVM_OBJECT_MUST_HAVE_CONSTRUCTOR \\
	+incdir+$(UVM_HOME)/src $(UVM_HOME)/src/uvm.sv \\
	-cm line+cond+fsm+branch+tgl -cm_dir ./coverage.vdb \\
	$(UVM_HOME)/src/dpi/uvm_dpi.cc -CFLAGS -DVCS

SIMV = ./simv +UVM_VERBOSITY=$(UVM_VERBOSITY) \\
	+UVM_TESTNAME=$(TEST) +UVM_TR_RECORD +UVM_LOG_RECORD \\
	+verbose=1 +ntb_random_seed=244 -l vcs.log

x:	comp run 

comp:
	$(VCS) +incdir+.+$(SRC) $(SRCS)

run:
	$(SIMV)

clean:
	rm -rf coverage.vdb csrc DVEfiles inter.vpd simv \\
	simv.daidir ucli.key vc_hdrs.h vcs.log .inter.vpd.uvm
"""
