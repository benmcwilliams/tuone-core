```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Glasgow-Caledonian-University" or company = "Glasgow Caledonian University")
sort location, dt_announce desc
```
