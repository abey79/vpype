eval "files=sorted(glob('cmyk_svgs/*.svg'))"
eval "cols=2; rows=ceil(len(files)/cols)"
eval "names={};n=100"
grid -o 10cm 15cm "%cols%" "%rows%"
  read --no-fail --no-crop "%files[_i] if _i < len(files) else ''%"
  layout 10x15cm
  forlayer
    eval "%if _name not in names: names[_name] = n; n = n+1%"
    lmove %_lid% "%names[_name]%"
  end
end
