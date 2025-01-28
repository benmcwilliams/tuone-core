```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Parthenope-University-of-Naples" or company = "Parthenope University of Naples")
sort location, dt_announce desc
```
