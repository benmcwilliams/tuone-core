```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "ESVAGT" or company = "ESVAGT")
sort location, dt_announce desc
```
