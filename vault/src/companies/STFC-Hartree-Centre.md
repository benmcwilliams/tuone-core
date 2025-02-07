```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "STFC-Hartree-Centre" or company = "STFC Hartree Centre")
sort location, dt_announce desc
```
