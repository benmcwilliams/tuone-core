```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solar-Integrated-Technologies" or company = "Solar Integrated Technologies")
sort location, dt_announce desc
```
