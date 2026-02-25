TOP=../..
include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE

#----------------------------------------------------
#  Optimization of db files using dbst (DEFAULT: NO)
#DB_OPT = YES

#----------------------------------------------------
# Create and install (or just install) into <top>/db
# databases, templates, substitutions like this
DB_INSTALLS += $(AUTOSAVE)/db/save_restoreStatus.db
DB_INSTALLS += $(ASYN)/db/asynRecord.db
DB_INSTALLS += $(EVG)/db/eventGenerator.db
DB += alsGblPVs.db
DB += alsGblPVsInjReqAssembly.db
DB += timing.db

ifneq ($(devIocStats),)
DB_INSTALLS += $(devIocStats)/db/ioc_stats.db
endif

ifneq ($(IOCSTATS),)
DB_INSTALLS += $(IOCSTATS)/db/iocAdminSoft.db
endif

ifneq ($(RECCASTER),)
DB_INSTALLS += $(RECCASTER)/db/reccaster.db
endif

#----------------------------------------------------
# If <anyname>.db template is not named <anyname>*.template add
# <anyname>_template = <templatename>

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

