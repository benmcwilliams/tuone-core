```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Huawei-Digital-Power" or company = "Huawei Digital Power")
sort location, dt_announce desc
```
