```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Institute for Solar Energy Research Hamelin (ISFH)"
sort location, dt_announce desc
```
