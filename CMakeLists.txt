project(mampy NONE)

include(RezBuild)
include(RezInstallPython)

file(GLOB_RECURSE pyfiles "mampy/*.py")
rez_install_python(
  py
  FILES
    ${pyfiles}
  DESTINATION .
  LOCAL_SYMLINK
  )
