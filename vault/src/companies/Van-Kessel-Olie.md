```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Van-Kessel-Olie" or company = "Van Kessel Olie")
sort location, dt_announce desc
```
