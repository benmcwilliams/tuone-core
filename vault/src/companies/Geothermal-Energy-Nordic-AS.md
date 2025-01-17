```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Geothermal Energy Nordic AS"
sort location, dt_announce desc
```
