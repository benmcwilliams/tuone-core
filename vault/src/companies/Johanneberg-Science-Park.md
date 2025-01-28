```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Johanneberg-Science-Park" or company = "Johanneberg Science Park")
sort location, dt_announce desc
```
