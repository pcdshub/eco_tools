'''
Utilities for creating GIT bare repos and such'''

import os
import re
import fileinput
import subprocess
import sys
from repo_defaults import *
from svn_utils import *
from version_utils import *

import gc

'''TODO: Fix error msg on svn epics-release:
fatal: Not a git repository (or any parent up to mount point /reg/g/pcds)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).'''

LCLS_TOOLS			= '/afs/slac/g/lcls/tools'
if 'TOOLS' in os.environ:
    TOOLS_SITE_TOP	= os.environ['TOOLS']
elif 'EPICS_TOOLS' in os.environ:
    TOOLS_SITE_TOP      = os.environ['EPICS_TOOLS']
else:
    TOOLS_SITE_TOP	= LCLS_TOOLS
    os.environ['TOOLS'] = TOOLS_SITE_TOP

# Configure the SSH proxy if in S3DF. Some of the EPICS development VMs don't have outside internet access
if os.path.exists('/sdf'):
    os.environ['GIT_SSH_COMMAND'] = f'ssh -F {os.path.dirname(__file__)}/ssh_config/config.s3df'

gitModulesTxtFile   = os.path.join( TOOLS_SITE_TOP, 'eco_modulelist', 'modulelist.txt' )

def parseGitModulesTxt():
    '''Parse the GIT modules txt file and return a dict of packageName -> location'''
    if not os.path.isfile( gitModulesTxtFile ):
        return {}
    package2Location = {}
    with open(gitModulesTxtFile, 'r') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        parts = line.split()
        if(len(parts) < 2):
            print("Error parsing ", gitModulesTxtFile, "Cannot break", line, "into columns with enough fields using spaces/tabs")
            continue
        packageName = parts[0]
        packageLocation = expandMacros( parts[1], os.environ )
        package2Location[packageName] = packageLocation
    return package2Location

git_package2Location = parseGitModulesTxt()

def determineGitRoot( ):
    '''Get the root folder for GIT repos at SLAC'''
    gitRoot = DEF_AFS_GIT_REPOS
    # The GIT_REPO_ROOT variable is mainly used when testing eco and is not something that we really expect from the environment.
    if "GIT_REPO_ROOT" in os.environ:
        gitRoot = os.environ["GIT_REPO_ROOT"]
    elif "GIT_TOP" in os.environ:
        gitRoot = os.environ["GIT_TOP"]
    return gitRoot

def git_call( gitCommand, gitDir=None, debug=False, *args, ** kwargs ):
    '''
    Run the specified git command via subprocess.call
    gitCommand can be a string or a list of strings.
    An initial "git" string will be provided if needed.
    Returns command status
    '''
    cmdList = []
    if type(gitCommand) is str:
        if not gitCommand.startswith( 'git ' ):
            cmdList = [ 'git' ]
        cmdList += gitCommand.split()
    else:
        if gitCommand[0] != 'git':
            cmdList = [ 'git' ]
        cmdList += gitCommand
    if gitDir is not None:
        cmdList.insert( 1, [ '--git-dir', gitDir ] )
    if debug:
        print("git_call running: %s" % ' '.join( cmdList ))
    callStatus = subprocess.call( cmdList, *args, **kwargs )
    if debug:
        print("git_call  status:", callStatus)
    return callStatus

def git_check_call( gitCommand, gitDir=None, debug=False, *args, ** kwargs ):
    '''
    Run the specified git command via subprocess.check_call
    gitCommand can be a string or a list of strings.
    An initial "git" string will be provided if needed.
    Returns cmd status code
    May throw RuntimeError or subprocess.CalledProcessError exceptions
    '''
    cmdList = []
    if isinstance( gitCommand, str ):
        if not gitCommand.startswith( 'git ' ):
            cmdList = [ 'git' ]
        cmdList += gitCommand.split()
    else:
        if gitCommand[0] != 'git':
            cmdList = [ 'git' ]
        cmdList += gitCommand
    if gitDir is not None:
        cmdList.insert( 1, [ '--git-dir', gitDir ] )
    if debug:
        print("git_check_call running: %s" % ' '.join( cmdList ))
    callStatus = subprocess.check_call( cmdList, *args, **kwargs )
    if debug:
        print("git_check_call  status:", callStatus)
    return callStatus

def git_check_output( gitCommand, gitDir=None, debug=False, *args, ** kwargs ):
    '''
    Run the specified git command via subprocess.check_output
    gitCommand can be a string or a list of strings.
    An initial "git" string will be provided if needed.
    Returns cmd output
    May throw RuntimeError or subprocess.CalledProcessError exceptions
    '''
    cmdList = []
    if type(gitCommand) is str:
        if not gitCommand.startswith( 'git ' ):
            cmdList = [ 'git' ]
        cmdList += gitCommand.split()
    else:
        if gitCommand[0] != 'git':
            cmdList = [ 'git' ]
        cmdList += gitCommand

    if gitDir is not None:
        cmdList.insert( 1, [ '--git-dir', gitDir ] )

    if debug:
        print("git_check_output running: %s" % ' '.join( cmdList ))

    git_output = subprocess.check_output( cmdList, *args, **kwargs )

    if debug:
        print(git_output)
    return git_output

def gitGetRemoteFile( url, refName, filePath, debug = False ):
    '''Fetchs a file from a git repo url.
    Returns file as a string or None if not found.'''
    fileContents = None
    try:
        commitSpec = refName + ':' + filePath
        fileContents = subprocess.check_output( [ 'git', '--git-dir=%s' % url, 'show', commitSpec ], stderr=subprocess.STDOUT )
    except OSError as e:
        if debug:
            print(e)
        pass
    except subprocess.CalledProcessError as e:
        if debug:
            print(e)
        pass
    return fileContents

def gitGetRemoteTags( url, debug = False, verbose = False ):
    '''Fetchs a list of tags from a git repo url.
    Returns a dictionary of SHA1 hashes by tagName.'''
    tagSpecRegExp = re.compile( r"^(.*)\s+refs/tags/(.*)$" )
    tags = {}
    try:
        if verbose:
            print("gitGetRemoteTags running: git ls-remote %s" % url)
        statusInfo = subprocess.check_output( [ 'git', 'ls-remote', url ], stderr=subprocess.STDOUT )
        for line in statusInfo.splitlines():
            if line is None:
                break
            tagSpecMatch = tagSpecRegExp.search( line.decode('utf-8') )
            if not tagSpecMatch:
                continue
            tags[ tagSpecMatch.group(2) ] = tagSpecMatch.group(1)

    except OSError as e:
        if debug:
            print(e)
        pass
    except subprocess.CalledProcessError as e:
        if debug:
            print(e)
        pass
    if verbose:
        print("gitGetRemoteTags: Found %d tags in %s" % ( len(tags), url ))
    return tags

def gitGetRemoteTag( url, tag, debug = False, verbose = False ):
    '''Fetchs tags from a git repo url and looks for a match w/ the desired tag.
    Returns a tuple of ( sha, tag ), ( None, None ) on error.
    For a matching git remote, url must be a valid string and tag must be found.'''
    tag_sha		= None
    git_url     = None
    git_tag     = None
    url_valid   = False
    if tag is None:
        tag         = 'HEAD'
        tag_spec    = tag
    else:
        tag_spec    = 'refs/tags/%s' % tag
    try:
        tags = gitGetRemoteTags( url, debug = debug, verbose = verbose )
        if tag in tags:
            git_url = url
            git_tag = tag
            tag_sha = tags[tag]

    except OSError as e:
        if debug:
            print(e)
        pass
    except subprocess.CalledProcessError as e:
        if debug:
            print(e)
        pass
    if verbose:
        if git_url:
            print("gitGetRemoteTag: Found git_tag %s %7.7s in git_url %s" % ( git_tag, tag_sha, git_url ))
        elif url_valid:
            print("gitGetRemoteTag: Unable to find tag %s in git url %s" % ( tag, url ))
        else:
            print("gitGetRemoteTag: Invalid git url %s" % ( url ))
    return ( tag_sha, git_tag )

def gitGetTagSha( tag ):
    tagSha = None
    try:
        # Get the tagSha
        cmdList = [ "git", "show-ref", tag ]
        gitOutput = subprocess.check_output( cmdList ).splitlines()
        if len(gitOutput) == 1:
            tagSha = gitOutput[0].split()[0]
    except:
        pass
    return tagSha

def initBareRepo( gitRepoPath, verbose=False ):
    if not gitRepoPath.endswith( ".git" ):
        raise Exception( "initBareRepo: repo path must end in .git\n%s" % gitRepoPath )
    if os.path.exists(gitRepoPath):
        raise Exception("Git repo path already exists at " + gitRepoPath)

    # Make sure parent folder exists
    ( parentFolder, module )  = os.path.split( gitRepoPath )
    if not os.path.isdir( parentFolder ):
        if verbose: print("Pre-creating parent folder for " + gitRepoPath)
        os.makedirs( parentFolder, 0o775 )

    if verbose: print("Creating a new bare repo in " + gitRepoPath)
    subprocess.check_call(["git", "init", "--bare", "--template=%s/templates" % DEF_GIT_MODULES_PATH, gitRepoPath])
    if not os.path.exists(gitRepoPath):
        raise Exception( "Failed to create git repo at:\n" + gitRepoPath )

def cloneUpstreamRepo( gitUpstreamRepo, tpath, packageName, branch=None, depth=None, verbose=False ):
    '''Create a clone of the upstream repo given a destination folder'''
    if packageName:
        clonedFolder = os.path.join(tpath, packageName)
    else:
        clonedFolder = tpath
    prompt = "Cloning the upstream repo at %s into %s" % ( gitUpstreamRepo, clonedFolder )
    gitCommand = "clone --recursive %s %s" % ( gitUpstreamRepo, clonedFolder )
    if branch:
        gitCommand += " --branch %s" % branch
        prompt += " from branch %s" % branch
        if gitGetVersionNumber() > 1.08:
            gitCommand += " --config advice.detachedHead=false"
    #if depth and gitUpstreamRepo.find('://') > 0:
    if depth:
        gitCommand += " --no-local --depth %d" % depth
    #May throw RuntimeError or subprocess.CalledProcessError exceptions
    print(prompt)
    #print "%s" % prompt
    git_check_call( gitCommand, debug=verbose )
    return clonedFolder

def createGitIgnore():
    gitIgnoreLines = [	
                        "*~",
                        "O.*/",
                        "*.log",
                        "*.swp",
                        "CVS/",
                        "bin/",
                        "db/",
                        "dbd/",
                        "html/",
                        "include/",
                        "lib/",
                        "templates/",
                        "cdCommands",
                        "envPaths",
                        "RELEASE_SITE",
                        "tags"
                    ]
    with open(".gitignore", "w") as f:
        f.write("\n".join(gitIgnoreLines))
    subprocess.check_call(['git', 'add', '.gitignore'])

def gitCommitAndPush( message ):
    '''Call git commit and git push'''
    subprocess.check_call(['git', 'commit', '-m', message ])
    message = 'Initial commit/import from eco. Added a default .gitignore and other defaults.'
    subprocess.check_call(['git', 'push' ])

def addPackageToEcoModuleList(packageName, gitUpstreamRepo):
    '''Add the package with the given upstream repo to eco's modulelist'''
    curDir = os.getcwd()
    print("Adding package", packageName, "to eco_modulelist")
    tools_dir = os.environ['TOOLS']
    if not tools_dir:
        print('addPackageToEcoModuleList Error: TOOLS env not defined.')
        return
    gitModulesTxtFolder = os.path.join(os.environ['TOOLS'], 'eco_modulelist')
    os.chdir(gitModulesTxtFolder)

    try:
        repoCmd = [ 'git', 'status', '--short', '--untracked-files=no' ]
        statusInfo = git_check_output( repoCmd, stderr=subprocess.STDOUT )
        statusLines = statusInfo.splitlines()
        if len(statusLines) > 0:
            repoCmd = [ 'git', 'commit', '-a', '-m', '"eco_tools addPackageToEcoModuleList: Committing uncommited changes"' ]
            git_check_call( repoCmd, stderr=subprocess.STDOUT )
    except:
        raise

    subprocess.check_call(['git', 'pull', '--rebase'])
    with open('modulelist.txt', 'a') as f:
        f.write(packageName + "\t\t\t" + gitUpstreamRepo+"\n")
    subprocess.check_call(['git', 'add', 'modulelist.txt'])
    subprocess.check_call(['git', 'commit', '-m', 'eco added package ' + packageName + ' located at ' + gitUpstreamRepo])
    subprocess.check_call(['git', 'pull', '--rebase'])
    subprocess.check_call(['git', 'push' ])
    os.chdir(curDir)

def createBranchFromTag( tag, branchName ):
    '''Checkout the tag and create a branch using the tag as a starting point.'''
    subprocess.check_call(['git', 'checkout', '-q', tag])
    subprocess.check_call(['git', 'checkout', '-b', branchName])

def gitGetWorkingBranch( debug = False, verbose = False ):
    '''See if the current directory is the top of an git working directory.
    Returns a 3-tuple of ( url, branch, tag ), ( None, None, None ) on error.
    For a valid git working dir, url must be a valid string, branch is the branch name or None if detached,
    tag is either None or a tag name if HEAD refers to a tag name.'''
    repo_url    = None
    repo_branch = None
    repo_tag    = None
    try:
        repoCmd = [ 'git', 'symbolic-ref', 'HEAD' ]
        statusInfo = subprocess.check_output( repoCmd, stderr=subprocess.STDOUT )
        statusLines = statusInfo.splitlines()
        if len(statusLines) > 0 and statusLines[0].startswith( 'refs/heads/' ):
            repo_branch = statusLines[0].split('/')[2]

        repoCmd = [ 'git', 'remote', '-v' ]
        statusInfo = subprocess.check_output( repoCmd, stderr=subprocess.STDOUT )
        statusLines = statusInfo.splitlines()
        for line in statusLines:
            if line is None:
                break
            tokens = line.split()
            if tokens[0] == 'origin':			# Use remote 'origin' if found
                repo_url = tokens[1]
                break
            if tokens[0].find('origin') >= 0:	# Backup is last remote containing 'origin'
                repo_url = tokens[1]
            if repo_url is None:				# If all else fails just use first remote
                repo_url = tokens[1]

        if repo_url:
            # Remove any trailing path separator
            ( repoPath, repoPkg ) = os.path.split( repo_url )
            if not repoPkg:
                repo_url = repoPath

        # See if HEAD corresponds to any tags
        statusInfo = subprocess.check_output( [ 'git', 'name-rev', '--name-only', '--tags', 'HEAD' ], stderr=subprocess.STDOUT )
        statusLines = statusInfo.splitlines()
        if len(statusLines) > 0:
            # Just grab the first tag that matches
            repo_tag = statusLines[0].split('^')[0]

    except OSError as e:
        if debug:
            print(e)
        pass
    except subprocess.CalledProcessError as e:
        if debug:
            print(e)
        pass
    return ( repo_url, repo_branch, repo_tag )

def determinePathToGitRepo( packagePath, verbose = False ):
    '''If the specified package is stored in GIT, then return the URL to the GIT repo. Otherwise, return None'''
    # See if the package was listed in $TOOLS/eco_modulelist/modulelist.txt
    packageName = os.path.split( packagePath )[-1]
    if packageName in git_package2Location:
        defRepoPath = git_package2Location[packageName]
        if os.path.isdir( defRepoPath ):
            return defRepoPath
        gitRoot = determineGitRoot()
        if gitRoot != DEF_AFS_GIT_REPOS and gitRoot != DEF_AFS_GIT_REPOS2:
            # See if we need to adjust the path from git_package2Location
            if  defRepoPath.startswith( DEF_AFS_GIT_REPOS ):
                defRepoPath = defRepoPath.replace(    DEF_AFS_GIT_REPOS, gitRoot )
            if  defRepoPath.startswith( DEF_AFS_GIT_REPOS2 ):
                defRepoPath = defRepoPath.replace(    DEF_AFS_GIT_REPOS2, gitRoot )
        return defRepoPath

    # Check under the root of the git repo area for a bare repo w/ the right name
    gitRoot = determineGitRoot()
    gitPackageDir  = packageName + ".git"
    gitPackagePath = packagePath + ".git"
    if not os.path.isdir( DEF_CVS_ROOT ) and gitRoot:
        # Must be offsite, assume gitRoot and an EPICS module path
        return os.path.join( gitRoot, 'package/epics/modules', gitPackageDir )
    for dirPath, dirs, files in os.walk( gitRoot, topdown=True ):
        if len( dirs ) == 0:
            continue
        for dir in dirs[:]:
            if dir == 'from-svn' or dir == 'from-cvs':
                # Remove from list so we don't search these import directories
                dirs.remove( dir )
                continue
            if os.path.isdir( os.path.join( dirPath, gitPackagePath ) ):
                return os.path.join( dirPath, gitPackagePath )
            if dir == gitPackagePath:
                return os.path.join( dirPath, dir )
            if dir.endswith( ".git" ):
                # Remove from list so we don't search recursively
                dirs.remove( dir )
    # Didn't find a match in eco_modulelist or git paths.
    # Check for an svn package
    (svn_url, svn_path, svn_tag) = svnFindPackageRelease( packagePath, tag = None, verbose=verbose )
    if svn_url:
        return svn_url
    return None

def gitFindPackageRelease( packageSpec, tag, debug = False, verbose = False ):
    (repo_url, repo_tag) = (None, None)
    if verbose:
        print("gitFindPackageRelease( packageSpec=%s, tag=%s )" % ( packageSpec, tag ))
    if tag:
        packagePath = packageSpec
    else:
        (packagePath, tag) = os.path.split( packageSpec )
    if tag:
        packageName = os.path.split( packagePath )[1]
    else:
        packageName = packagePath
    if verbose:
        print("gitFindPackageRelease: packageName=%s, packagePath=%s" % ( packageName, packagePath ))

    # See if the package was listed in $TOOLS/eco_modulelist/modulelist.txt
    if packageName in git_package2Location:
        url_path = determinePathToGitRepo( packageName, verbose=verbose )
        (repo_sha, repo_tag) = gitGetRemoteTag( url_path, tag, verbose=verbose )
        if repo_sha:
            repo_url = url_path
    else:
        for url_root in [ DEF_GIT_MODULES_PATH, DEF_GIT_EXTENSIONS_PATH, DEF_GIT_EPICS_PATH, DEF_GIT_REPO_PATH ]:
            if repo_url is not None:
                break
            for p in [ packageName, packagePath ]:
                url_path = '%s/%s.git' % ( url_root, p )
                (repo_sha, repo_tag) = gitGetRemoteTag( url_path, tag, verbose=verbose )
                if repo_sha is not None:
                    repo_url = url_path
                    break
                if packageName == packagePath:
                    break

    if verbose:
        if repo_url:
            print("gitFindPackageRelease found %s/%s: url=%s, tag=%s" % ( packagePath, tag, repo_url, repo_tag ))
        else:
            print("gitFindPackageRelease Error: Cannot find %s/%s" % (packagePath, tag))
    return (repo_url, repo_tag)

def git_get_versionFileName():
    '''If git config has a value for ecotools.versionfile,
    this routine returns it.  If not, returns None'''
    versionFileName = None
    try:
        git_output = git_check_output( "git rev-parse --show-toplevel" ).splitlines()
        if len(git_output) >= 1:
            # Try reading versionFileName from the new softlink .versionFile
            versionFileName = os.readlink( os.path.join( git_output[0], '.versionFile' ) )
    except:
        pass

    # Backup versionFileName is original git config setting ecotools.versionfile
    try:
        if versionFileName is None:
            git_output = git_check_output( "git config --get ecotools.versionfile" ).splitlines()
            if len(git_output) >= 1:
                versionFileName = git_output[0]
    except:
        pass
    return versionFileName

def gitGetVersion():
    '''Run git --version and return the git version as a string
    Returns None on error'''
    version = None
    try:
        git_output = git_check_output( "git --version" ).splitlines()
        if len(git_output) >= 1:
            version = git_output[0].split()[-1]
    except:
        pass
    return version

def gitGetVersionNumber():
    '''Run git --version and return the git version as a float.
    Each decimal point scales subsequent version components by 0.01 
    1.2.3.4 => 1.020304
    Returns 0.0 on error'''
    version = gitGetVersion()
    if not version:
        return 0.0
    return VersionToRelNumber( version )

