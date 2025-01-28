```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "BW-Offshore-Norway-AS" or company = "BW Offshore Norway AS")
sort location, dt_announce desc
```
