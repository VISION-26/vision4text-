import React from 'react';

const Table = ({
    columns = [],
    data = [],
    loading = false,
    emptyMessage = 'No records found.'
}) => {
    return (
        <div className="w-full overflow-x-auto border border-slate-100 dark:border-slate-800 rounded-2xl bg-white dark:bg-[#0d1b38] transition-colors duration-300 font-sans shadow-soft">
            <table className="w-full min-w-[600px] border-collapse text-left text-sm">
                <thead>
                    <tr className="border-b border-slate-105 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/10">
                        {columns.map((col) => (
                            <th
                                key={col.key}
                                className={`py-3.5 px-6 font-semibold text-slate-500 dark:text-slate-400 capitalize text-xs tracking-wider ${col.className || ''}`}
                            >
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                    {loading ? (
                        <tr>
                            <td colSpan={columns.length} className="py-12 text-center text-slate-400 font-medium">
                                <div className="flex flex-col items-center justify-center gap-3">
                                    <div className="w-8 h-8 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
                                    <span>Loading data...</span>
                                </div>
                            </td>
                        </tr>
                    ) : data.length === 0 ? (
                        <tr>
                            <td colSpan={columns.length} className="py-12 text-center text-slate-400 text-xs font-medium">
                                {emptyMessage}
                            </td>
                        </tr>
                    ) : (
                        data.map((row, idx) => (
                            <tr
                                key={row.id || idx}
                                className="hover:bg-slate-50/50 dark:hover:bg-slate-800/10 transition-colors"
                            >
                                {columns.map((col) => (
                                    <td key={col.key} className={`py-4 px-6 ${col.className || ''}`}>
                                        {col.render ? col.render(row) : row[col.key]}
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default Table;
