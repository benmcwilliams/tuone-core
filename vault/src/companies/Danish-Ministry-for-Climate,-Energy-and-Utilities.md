```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Danish-Ministry-for-Climate,-Energy-and-Utilities" or company = "Danish Ministry for Climate, Energy and Utilities")
sort location, dt_announce desc
```
