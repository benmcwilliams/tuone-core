```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "SHINE-Technologies" or company = "SHINE Technologies")
sort location, dt_announce desc
```
