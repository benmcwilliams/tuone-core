```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Netherlands Organisation for Applied Scientific Research (TNO)"
sort location, dt_announce desc
```
