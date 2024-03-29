'''
Defaults for release paths, repo urls and repo paths'''
# repo_defaults.py

import os

# Default string variables for cvs, svn, and git repo paths
DEF_CVS_ROOT		= '/afs/slac/g/lcls/cvs'
DEF_SVN_REPO		= "file:///afs/slac/g/pcds/vol2/svn/pcds"
DEF_SVN_REPOS		= [ DEF_SVN_REPO ]
DEF_SVN_STUB1		= "epics/trunk"
DEF_SVN_STUB2		= "trunk/pcds/epics"
DEF_SVN_TAGS		= "/".join( [ DEF_SVN_REPO, "epics/tags" ])

DEF_EPICS_TOP_AFS	= "/afs/slac.stanford.edu/g/pcds/epics"
DEF_EPICS_TOP_LCLS  = "/afs/slac.stanford.edu/g/lcls/epics"
DEF_EPICS_TOP_MCC   = "/usr/local/lcls/epics"
DEF_EPICS_TOP_PCDS	= "/cds/group/pcds/epics"
DEF_EPICS_TOP_PCDS_OLD	= "/reg/g/pcds/epics"
DEF_LCLS_GROUP_OWNER= "lcls"
DEF_LCLS_TOOLS		= '/afs/slac.stanford.edu/g/lcls/tools'
DEF_LCLS_CRAM_DIR	= DEF_LCLS_TOOLS + '/script/multi_facility_deploy'
DEF_LCLS_CRAM_CFG	= DEF_LCLS_CRAM_DIR	+ '/facilities.cfg'
DEF_LCLS_CRAM_USER	= '.cram_user_facilities.cfg'
DEF_PCDS_GROUP_OWNER= "ps-pcds"

# Use these for filesystem access
DEF_AFS_GIT_REPOS		= "/afs/slac.stanford.edu/g/cd/swe/git/repos"
DEF_AFS_GIT_REPOS2		= "/afs/slac/g/cd/swe/git/repos"

DEF_GIT_EXT_TOP_TAG		= "slac-trunk"
DEF_GIT_RELEASE_DEPTH = 10

DEF_GIT_REPO_PATH		= DEF_AFS_GIT_REPOS
if "GIT_REPO_ROOT" in os.environ:
    DEF_GIT_REPO_PATH = os.environ["GIT_REPO_ROOT"]
elif "GIT_TOP" in os.environ:
    DEF_GIT_REPO_PATH = os.environ["GIT_TOP"]
DEF_GIT_EPICS_PATH		= DEF_GIT_REPO_PATH + "/package/epics"
DEF_GIT_BASE_PATH		= DEF_GIT_REPO_PATH + "/package/epics/base"
DEF_GIT_MODULES_PATH	= DEF_GIT_REPO_PATH + "/package/epics/modules"
DEF_GIT_EXTENSIONS_PATH	= DEF_GIT_REPO_PATH + "/package/epics/extensions"
DEF_GIT_EXT_TOP_PATH	= DEF_GIT_EXTENSIONS_PATH + "/extensions-top.git"

# Use these for remote repo access
#DEF_GIT_REPOS_URL		= "file://" + DEF_GIT_REPO_PATH
##DEF_GIT_REPOS_URL		= "git@code.stanford.edu:slac-epics"
#DEF_GIT_EPICS_URL		= "file://" + DEF_GIT_EPICS_PATH
#DEF_GIT_MODULES_URL		= "file://" + DEF_GIT_MODULES_PATH
#DEF_GIT_EXTENSIONS_URL	= "file://" + DEF_GIT_EXTENSIONS_PATH
#DEF_GIT_EXT_TOP_URL		= "file://" + DEF_GIT_EXTENSIONS_PATH + "/extensions-top.git"

defEpicsTopVariants = []
defEpicsTopVariants.append( "modules" )
defEpicsTopVariants.append( "extensions" )
defEpicsTopVariants.append( "iocTop" )
defEpicsTopVariants.append( "ioc" )
defEpicsTopVariants.append( "ioc/common" )
defEpicsTopVariants.append( "ioc/amo" )
defEpicsTopVariants.append( "ioc/sxr" )
defEpicsTopVariants.append( "ioc/xpp" )
defEpicsTopVariants.append( "ioc/cxi" )
defEpicsTopVariants.append( "ioc/mec" )
defEpicsTopVariants.append( "ioc/mfx" )
defEpicsTopVariants.append( "ioc/xcs" )
defEpicsTopVariants.append( "ioc/xrt" )
defEpicsTopVariants.append( "ioc/tst" )
defEpicsTopVariants.append( "ioc/fee" )
defEpicsTopVariants.append( "ioc/las" )
defEpicsTopVariants.append( "screens" )
defEpicsTopVariants.append( "screens/edm" )

