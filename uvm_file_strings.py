##########
# TB_TOP #
##########
tb_string = """
`include "uvm_macros.svh"
import uvm_pkg::*;

module {0}_tb_top;
  logic clk, reset;
  parameter CLK_PERIOD = 10;

  // Interface declarations
  
  //// CHANGEME ////
  
  // the DUT
  
  //// CHANGEME ////
  
  initial begin
    //Registers the Interface in the configuration block so that other
    //blocks can use it
    
    // e.g. uvm_resource_db#(virtual simpleadder_if)::set
    // (.scope("ifs"), .name("simpleadder_if"), .val(vif));
    
    //Executes the test
    run_test();
  end
  
  //Variable initialization
  initial begin
    clk = 1'b0;
    reset = 1'b1;
    #CLK_PERIOD reset = 1'b1;
    #(CLK_PERIOD/2) reset = 1'b0;
  end
  
  //Clock generation
  always
    #(CLK_PERIOD/2) clk = ~clk;
endmodule
"""

##########
# TEST   #
##########
test_string = """
class {0}_test extends uvm_test;
  `uvm_component_utils({0}_test)

  {0}_env {1}_env;

  function new(string name, uvm_component parent);
    super.new(name, parent);

    uvm_resource_db#(int)::set(.scope("params"), .name("num_transactions"), .val(15));
  endfunction: new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    {1}_env = {0}_env::type_id::create(.name("{1}_env"), .parent(this));
  endfunction: build_phase

  task run_phase(uvm_phase phase);
    {0}_sequence {1}_seq;

    phase.raise_objection(.obj(this));
    {1}_seq = {0}_sequence::type_id::create(.name("{1}_seq"), .contxt(get_full_name()));
    assert({1}_seq.randomize());
    {1}_seq.start({1}_env.{1}_agent.{1}_seqr);
    phase.drop_objection(.obj(this));
  endtask: run_phase
endclass: {0}_test
"""

env_string = """
class {0}_env extends uvm_env;
  `uvm_component_utils({0}_env)

  {0}_agent {1}_agent;
  {0}_scoreboard {1}_sb;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction: new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    {1}_agent= {0}_agent::type_id::create(.name("{1}_agent"), .parent(this));
    {1}_sb= {0}_scoreboard::type_id::create(.name("{1}_sb"), .parent(this));
  endfunction: build_phase

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    {1}_agent.agent_ap_before.connect({1}_sb.sb_export_before);
    {1}_agent.agent_ap_after.connect({1}_sb.sb_export_after);
  endfunction: connect_phase
endclass: {0}_env
"""

agent_string = """
class {0}_agent extends uvm_agent;
  `uvm_component_utils({0}_agent)

  uvm_analysis_port#({0}_transaction) agent_ap_before;
  uvm_analysis_port#({0}_transaction) agent_ap_after;

  {0}_sequencer {1}_seqr;
  {0}_driver {1}_drvr;
  {0}_monitor_before {1}_mon_before;
  {0}_monitor_after {1}_mon_after;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction: new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    agent_ap_before = new(.name("agent_ap_before"), .parent(this));
    agent_ap_after = new(.name("agent_ap_after"), .parent(this));

    {1}_seqr= {0}_sequencer::type_id::create(.name("{1}_seqr"), .parent(this));
    {1}_drvr= {0}_driver::type_id::create(.name("{1}_drvr"), .parent(this));
    {1}_mon_before= {0}_monitor_before::type_id::create(.name("{1}_mon_before"), .parent(this));
    {1}_mon_after= {0}_monitor_after::type_id::create(.name("{1}_mon_after"), .parent(this));
  endfunction: build_phase

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    {1}_drvr.seq_item_port.connect({1}_seqr.seq_item_export);
    {1}_mon_before.mon_ap_before.connect(agent_ap_before);
    {1}_mon_after.mon_ap_after.connect(agent_ap_after);
  endfunction: connect_phase
endclass: {0}_agent
"""

scoreboard_string = """
`uvm_analysis_imp_decl(_before)
`uvm_analysis_imp_decl(_after)

class {0}_scoreboard extends uvm_scoreboard;

  uvm_analysis_export #({0}_transaction) sb_export_before;
  uvm_analysis_export #({0}_transaction) sb_export_after;

  uvm_tlm_analysis_fifo #({0}_transaction) before_fifo;
  uvm_tlm_analysis_fifo #({0}_transaction) after_fifo;

  {0}_transaction transaction_before;
  {0}_transaction transaction_after;

  int repetitions;
  bit count_tx_enable;

  `uvm_component_utils_begin({0}_scoreboard)
    `uvm_field_int(count_tx_enable, UVM_ALL_ON)
  `uvm_component_utils_end

  function new(string name, uvm_component parent);
    super.new(name, parent);

    transaction_before= new("transaction_before");
    transaction_after= new("transaction_after");

    repetitions = 0;
    count_tx_enable = 0;
  endfunction: new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    sb_export_before= new("sb_export_before", this);
    sb_export_after= new("sb_export_after", this);

    before_fifo= new("before_fifo", this);
    after_fifo= new("after_fifo", this);
  endfunction: build_phase

  function void connect_phase(uvm_phase phase);
    sb_export_before.connect(before_fifo.analysis_export);
    sb_export_after.connect(after_fifo.analysis_export);
  endfunction: connect_phase

  function void check_phase(uvm_phase phase);
    int num_transactions;

    void'(uvm_resource_db#(int)::read_by_name
	  (.scope("params"), .name("num_transactions"), .val(num_transactions)));

    if (count_tx_enable) begin
	    assert (repetitions==num_transactions)
      	      else `uvm_error("{1}_scoreboard",
			      $sformatf("Not all transactions have been compared %0d of %0d.",
					repetitions,
					num_transactions)
			      );
    end
  endfunction // check_phase

  task run();
    forever begin
      before_fifo.get(transaction_before);
      after_fifo.get(transaction_after);

      compare();
    end
  endtask: run

  virtual function void compare();
    repetitions = repetitions + 1;
    if(transaction_before.equals(transaction_after)) begin
      `uvm_info("compare", {{"Test: OK!"}}, UVM_LOW);
    end else begin
      `uvm_fatal("compare", {{"Test: Fail!"}});
    end
  endfunction: compare
endclass: {0}_scoreboard
"""

driver_string = """
class {0}_driver extends uvm_driver#({0}_transaction);
  `uvm_component_utils({0}_driver)

  // declare a virtual interface

  //// CHANGEME ////

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction: new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // load an interface instance from the database

    //e.g. void'(uvm_resource_db#(virtual {0}_if)::read_by_name
    //(.scope("ifs"), .name("{0}_if"), .val(vif)));
    //// CHANGEME ////

  endfunction: build_phase

  task run_phase(uvm_phase phase);
    drive();
  endtask: run_phase

  virtual task drive();
    {0}_transaction {1}_tx;

    forever begin
      //@(posedge vif.sig_clock)
      seq_item_port.get_next_item({1}_tx);
      `uvm_info("{1}_driver", {1}_tx.sprint(), UVM_LOW);
      seq_item_port.item_done();
    end
  endtask: drive
endclass: {0}_driver
"""

monitor_string = """
class {0}_monitor_before extends uvm_monitor;
  `uvm_component_utils({0}_monitor_before)

  uvm_analysis_port#({0}_transaction) mon_ap_before;

  // declare a virtual interface

  //// CHANGEME ////

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction: new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // load an interface instance from the database
    //e.g. void'(uvm_resource_db#(virtual {0}_if)::read_by_name
    //(.scope("ifs"), .name("{0}_if"), .val(vif)));
    //// CHANGEME ////

    mon_ap_before = new(.name("mon_ap_before"), .parent(this));
  endfunction: build_phase

  task run_phase(uvm_phase phase);
    integer counter_mon = 0, state = 0;

    {0}_transaction {1}_tx;

    //forever begin
      //@(posedge vif.sig_clock)
        // if something happens begin
        //   {1}_tx = new();
        //   modify {1}_tx
        //   mon_ap_before.write({1}_tx);
        // end
    //end
  endtask: run_phase
endclass: {0}_monitor_before

class {0}_monitor_after extends uvm_monitor;
  `uvm_component_utils({0}_monitor_after)

  uvm_analysis_port#({0}_transaction) mon_ap_after;

  // declare a virtual interface

  //// CHANGEME ////

  {0}_transaction {1}_tx;

  //For coverage
  {0}_transaction {1}_tx_cg;

  //Define coverpoints
  covergroup {0}_cg;
    // e.g. ina_cp:     coverpoint {1}_tx_cg.ina;
    // e.g. inb_cp:     coverpoint {1}_tx_cg.inb;
    // e.g. cross ina_cp, inb_cp;
  endgroup: {0}_cg

  function new(string name, uvm_component parent);
    super.new(name, parent);
    {0}_cg = new;
  endfunction: new

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // load an interface instance from the database
    //e.g. void'(uvm_resource_db#(virtual {0}_if)::read_by_name
    //(.scope("ifs"), .name("{0}_if"), .val(vif)));
    //// CHANGEME ////

    mon_ap_after= new(.name("mon_ap_after"), .parent(this));
  endfunction: build_phase

  task run_phase(uvm_phase phase);
    integer counter_mon = 0, state = 0;
    {1}_tx = {0}_transaction::type_id::create(.name("{1}_tx"), .contxt(get_full_name()));

    //forever begin
      // @(posedge vif.sig_clock)

      // modify {1}_tx

      // mon_ap_after.write({1}_tx);
    //end
  endtask: run_phase

  virtual function void predictor();
    // e.g. {1}_tx.out = {1}_tx.ina + {1}_tx.inb;
  endfunction: predictor
endclass: {0}_monitor_after
"""

sequencer_string = """
class {0}_transaction extends uvm_sequence_item;
  `uvm_object_utils({0}_transaction)
  // e.g. rand bit[1:0] in;
  // e.g. bit[2:0] out;

  function new(string name = "");
    super.new(name);
  endfunction: new

  // e.g. `uvm_object_utils_begin({0}_transaction)
  // e.g.   `uvm_field_int(in, UVM_ALL_ON)
  // e.g.   `uvm_field_int(out, UVM_ALL_ON)
  // e.g. `uvm_object_utils_end

  function logic equals({0}_transaction rhs);
	// e.g. logic ret = data == rhs.data;
    logic ret = 1'b0;
	return ret;
  endfunction // equals

endclass: {0}_transaction

class {0}_sequence extends uvm_sequence#({0}_transaction);
  `uvm_object_utils({0}_sequence)

  int repetitions;

  function new(string name = "");
    super.new(name);
  endfunction: new

  task body();
    {0}_transaction {1}_tx;

    void'(uvm_resource_db#(int)::read_by_name
	  (.scope("params"), .name("num_transactions"), .val(repetitions)));

    //// CHANGEME ////
    repeat(repetitions) begin
      {1}_tx = {0}_transaction::type_id::create(.name("{1}_tx"), .contxt(get_full_name()));

      start_item({1}_tx);
      assert({1}_tx.randomize());
      //`uvm_info("{1}_sequence", {1}_tx.sprint(), UVM_LOW);
      finish_item({1}_tx);
    end
  endtask: body
endclass: {0}_sequence

typedef uvm_sequencer#({0}_transaction) {0}_sequencer;
"""
