#!../../bin/RL8-x86_64/timing
##!../../bin/linux-x86_64/timing

###############################################################################
# Set up environment

< envPaths

epicsEnvSet("EPICS_CA_MAX_ARRAY_BYTES", "1060000")
epicsEnvSet("AUTOSAVE_PATH", "$(AUTOSAVE_PATH=$(TOP)/autosave)")
epicsEnvSet("DB_TOP", "$(TOP)/db")
epicsEnvSet("TARGET_TOP", "$(TOP)")
epicsEnvSet("IOCSH_TOP", "$(SITEAPPS)/iocsh")
epicsEnvSet("IOCSH_LOCAL_TOP", "$(TOP)/iocsh")
epicsEnvSet("ENGINEER", "lucasrusso")
epicsEnvSet("LOCATION", "")
epicsEnvSet("WIKI", "DualTiming")
epicsEnvSet("IOCNAME", "DualTiming")

###############################################################################
# Register all support components
cd "${TOP}/iocBoot/${IOC}"
dbLoadDatabase("$(TOP)/dbd/timing.dbd")
timing_registerRecordDeviceDriver(pdbbase)

##############################################################################
# Load generic support modules
iocshLoad("$(IOCSH_TOP)/iocStatsAdmin.iocsh",  "IOCNAME=$(IOCNAME), DATABASE_TOP=$(DB_TOP)")
iocshLoad("$(IOCSH_TOP)/reccaster.iocsh", "IOCNAME=$(IOCNAME), DATABASE_TOP=$(DB_TOP)")
iocshLoad("$(IOCSH_TOP)/iocLog.iocsh",    "IOCNAME=$(IOCNAME), LOG_INET=$(LOG_DEST), LOG_INET_PORT=$(LOG_PORT)")
iocshLoad("$(IOCSH_TOP)/caPutLog.iocsh",  "IOCNAME=$(IOCNAME), LOG_INET=$(LOG_DEST), LOG_INET_PORT=$(LOG_PORT)")
iocshLoad("$(IOCSH_TOP)/autosave.iocsh", "AS_TOP=$(AUTOSAVE_PATH),IOCNAME=$(IOCNAME),DATABASE_TOP=$(DB_TOP),SEQ_PERIOD=60")

##############################################################################
# Declare addresss of each instance
# ONE LINE HERE FOR EACH INSTANCE

epicsEnvSet("T", "$(DUAL_TIMING_IOC_TEST=)")
epicsEnvSet("IP", "$(IP=131.243.93.169)")
epicsEnvSet("P", "$(T)$(P=EVG:)")
epicsEnvSet("R", "$(R=)")
epicsEnvSet("PORT", "$(PORT=$(P)$(R))")
epicsEnvSet("SEQ_DEBUG", "$(SEQ_DEBUG=0)")

##############################################################################
# Configure instances and load databases
# ONE LINE HERE FOR EACH INSTANCE
iocshLoad("$(IOCSH_LOCAL_TOP)/timing.iocsh", "PORT=$(PORT),P=$(P),R=$(R),IP=$(IP)")

###############################################################################
# Start IOC
iocInit()

###############################################################################
# Configure some modules after iocInit
iocshLoad("$(IOCSH_TOP)/after_iocInit.iocsh")

###############################################################################
# Start timing sequence program
dbpf "$(T)InjSeqDebug" $(SEQ_DEBUG)
seq timingSequence "P=$(P),R=$(R),T=$(T)"
