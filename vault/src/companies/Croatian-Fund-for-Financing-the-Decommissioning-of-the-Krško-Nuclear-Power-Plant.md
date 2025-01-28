```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Croatian-Fund-for-Financing-the-Decommissioning-of-the-Krško-Nuclear-Power-Plant" or company = "Croatian Fund for Financing the Decommissioning of the Krško Nuclear Power Plant")
sort location, dt_announce desc
```
