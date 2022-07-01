eval "names={};n=100"
forfile "cmyk_svgs/*.svg"
  read %_path%
  forlayer
    eval "%if _name not in names: names[_name] = n; n = n+1%"
    lmove %_lid% "%names[_name]%"
  end
end