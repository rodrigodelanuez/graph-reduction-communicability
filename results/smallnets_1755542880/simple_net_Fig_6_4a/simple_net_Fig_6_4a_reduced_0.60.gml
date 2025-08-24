graph [
  node [
    id 0
    label "8"
  ]
  node [
    id 1
    label "11"
  ]
  node [
    id 2
    label "('1','2')"
  ]
  node [
    id 3
    label "('0','7')"
  ]
  node [
    id 4
    label "((('10', (('3', '4'), '9')), '5'),'6')"
  ]
  edge [
    source 0
    target 1
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 1
    target 3
  ]
  edge [
    source 1
    target 4
  ]
  edge [
    source 2
    target 3
  ]
  edge [
    source 2
    target 4
  ]
  edge [
    source 3
    target 4
  ]
]
