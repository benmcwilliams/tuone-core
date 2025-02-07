```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ludwig-Maximilians-University" or company = "Ludwig Maximilians University")
sort location, dt_announce desc
```
