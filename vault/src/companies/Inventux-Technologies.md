```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Inventux-Technologies" or company = "Inventux Technologies")
sort location, dt_announce desc
```
