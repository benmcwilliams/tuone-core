```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "FlexH2" or company = "FlexH2")
sort location, dt_announce desc
```
