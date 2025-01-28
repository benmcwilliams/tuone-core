```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Pacific-Green-Technologies" or company = "Pacific Green Technologies")
sort location, dt_announce desc
```
