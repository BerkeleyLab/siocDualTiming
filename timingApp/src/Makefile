TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = timing
# timing.dbd will be created and installed
DBD += timing.dbd

# timing.dbd will be made up from these files:
timing_DBD += base.dbd

# Include dbd files from all support applications:
timing_DBD += timingSequence.dbd
timing_DBD += gunbunchdelays_wf.dbd
timing_DBD += eventGeneratorSup.dbd
timing_DBD += drvAsynIPPort.dbd
timing_DBD += asyn.dbd
timing_DBD += asSupport.dbd

# Add all the support libraries needed by this IOC
timing_LIBS += eventGeneratorSup
timing_LIBS += asyn
timing_LIBS += autosave
timing_LIBS += seq

ifneq ($(RECCASTER),)
    timing_DBD += reccaster.dbd
    timing_LIBS += reccaster
endif

ifneq ($(CAPUTLOG),)
    timing_DBD += caPutLog.dbd
    timing_LIBS += caPutLog
endif

ifneq ($(CALC),)
    timing_DBD += calc.dbd
    timing_LIBS += calc
endif

ifneq ($(AUTOSAVE),)
    timing_DBD += asSupport.dbd
    timing_LIBS += autosave
endif

ifneq ($(devIocStats),)
    dsbpm_DBD += devIocStats.dbd
    dsbpm_LIBS += devIocStats
endif

ifneq ($(IOCSTATS),)
    timing_DBD += devIocStats.dbd
    timing_LIBS += devIocStats
endif

ifneq ($(IOCEXIT),)
    timing_DBD += iocExit.dbd
    timing_LIBS += iocExit
endif

# timing_registerRecordDeviceDriver.cpp derives from timing.dbd
timing_SRCS += timingSequence.st
timing_SRCS += assemble_injreq.c
timing_SRCS += gunbunchdelays_wf.c
timing_SRCS += timing_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
timing_SRCS_DEFAULT += timingMain.cpp

ifdef EPICS_QSRV_MAJOR_VERSION
    timing_LIBS += qsrv
    timing_LIBS += $(EPICS_BASE_PVA_CORE_LIBS)
    timing_DBD += PVAServerRegister.dbd
    timing_DBD += qsrv.dbd
endif

# Finally link to the EPICS Base libraries
timing_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
timingSequence.c: TimingLookups.h
TimingLookups.h: ../TuningModeTriggers.csv ../parseTuningModeTriggers.py
	cd .. ; python parseTuningModeTriggers.py
