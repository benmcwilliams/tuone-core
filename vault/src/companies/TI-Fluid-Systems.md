```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "TI-Fluid-Systems" or company = "TI Fluid Systems")
sort location, dt_announce desc
```
