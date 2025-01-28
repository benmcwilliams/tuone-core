```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "OrangeGas" or company = "OrangeGas")
sort location, dt_announce desc
```
