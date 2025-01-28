```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sun-Age-Srl" or company = "Sun Age Srl")
sort location, dt_announce desc
```
