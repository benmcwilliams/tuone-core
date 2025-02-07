```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Organic-Electronic-Technologies" or company = "Organic Electronic Technologies")
sort location, dt_announce desc
```
