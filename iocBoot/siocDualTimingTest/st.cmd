#!../../bin/RL8-x86_64/timing
##!../../bin/linux-x86_64/timing

###############################################################################
# Set up environment
epicsEnvSet "T" "$(DUAL_TIMING_IOC_TEST=test)"
epicsEnvSet "EVG_ADDRESS" "$(EVG_ADDRESS=192.168.1.146)"
< envPaths
epicsEnvSet "IOCSH_PS1" "$(IOC)> "
epicsEnvSet DB_TOP "$(TOP)/db"
epicsEnvSet ENGINEER "jmweber"
epicsEnvSet LOCATION "SoftIOC"
epicsEnvSet WIKI "DualEventGenerator"
epicsEnvSet IOCNAME "DualTiming"

###############################################################################
# Conditionals
epicsEnvSet "SEQ_DEBUG" "$(SEQ_DEBUG=0)"

###############################################################################
# Register all support components
cd "$(TOP)"
dbLoadDatabase "dbd/timing.dbd"
timing_registerRecordDeviceDriver pdbbase
#pid_check("/vxboot/run/$(IOC).pid")

###############################################################################
# Set up ASYN port
# Port name, IP address, priority
eventGeneratorConfigure("EVG01", "$(EVG_ADDRESS)", 0)
asynSetTraceIOMask("EVG01_CMD",-1,0x4)
asynSetTraceMask("EVG01_CMD",-1,0x1)
asynSetTraceIOMask("EVG01_SEQ",-1,0x4)
asynSetTraceMask("EVG01_SEQ",-1,0x1)

###############################################################################
# Load record instances
dbLoadRecords("db/eventGenerator.db","P=$(T),R=EVG:,PORT=EVG01")
dbLoadRecords("db/timing.db","P=$(T),R=EVG:,T=$(T)")
dbLoadRecords("db/alsGblPVs.db","T=$(T)")
dbLoadRecords("db/alsGblPVsInjReqAssembly.db","T=$(T)")

##############################################################################
# Load additional records
iocshLoad "$(IOCSH_TOP)/als_default.iocsh"
dbLoadRecords "db/asynRecord.db" "P=$(IOC),R=:asyn,PORT=EVG01_CMD,ADDR=-1,IMAX=0,OMAX=0"

###############################################################################
# Start IOC
cd "${TOP}/iocBoot/${IOC}"
iocInit

###############################################################################
# Update IOC data
dbl >"/vxboot/PVnames/$(IOCNAME)"
epicsEnvShow >"/vxboot/PVenv/$(IOCNAME).softioc"
date

###############################################################################
# Start timing sequence program
dbpf "$(T)InjSeqDebug" $(SEQ_DEBUG)
seq timingSequence "P=$(T)EVG,R=:,T=$(T)"
